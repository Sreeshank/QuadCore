import hashlib
import re
from decimal import Decimal
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import current_user, create_demo_session, bearer
from app.core.config import settings
from app.db.session import get_db
from app.models import User, TaxProfile, Document, ReadinessReport, ValidationIssue, DemoSession, uid
from app.schemas import ProfileInput, DemoInput, VerifyInput, IssueUpdate, ChatInput, MONEY_FIELDS, normalize
from app.services import storage
from app.services.audit import record
from app.services.rules import CRITICAL
from app.services.extraction import validate_file, process_document
from app.services.rules import summarize, documents, document_verified, serialize_issue
from app.services.reports import make_pdf
from app.services.assistant import answer
from app.services.user_assistant import user_key_answer
from app.services.demo import seed_demo, SAMPLES, sample_pdf

router = APIRouter(prefix='/api/v1')


def profile_for(db, user):
    profile = db.scalar(select(TaxProfile).where(TaxProfile.user_id == user.id))
    if not profile:
        raise HTTPException(404, 'Complete your financial profile to get started')
    return profile


def doc_for(db, user, identifier):
    document = db.scalar(select(Document).where(Document.id == identifier, Document.user_id == user.id))
    if not document:
        raise HTTPException(404, 'Document not found')
    return document


def profile_json(profile):
    return {'id': profile.id, 'financial_year': profile.financial_year, 'answers': profile.answers_json}


def safe_name(name):
    return re.sub(r'[^\w.() -]', '_', name.replace('\\','/').split('/')[-1])[:160] or 'document'


def mask_pan(value):
    return re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', lambda m: m[0][:2] + '******' + m[0][-2:], value)


def doc_json(doc):
    return {'id': doc.id, 'filename': mask_pan(doc.filename), 'document_type': doc.document_type, 'processing_status': doc.processing_status, 'mime_type': doc.mime_type, 'created_at': doc.created_at.isoformat(), 'error_message': doc.error_message, 'missing_fields': sorted(CRITICAL.get(doc.document_type, {'financial_year'}) - {f.field_name for f in doc.fields}), 'fields': [
        {'id': f.id,'field_name': f.field_name, 'value': mask_pan(f.normalized_value), 'source_document_id': doc.id, 'source_page': f.source_page, 'extraction_method': f.extraction_method, 'verification_status': f.verification_status, 'review_indicator': f.review_indicator, 'evidence': mask_pan(f.evidence)}
        for f in doc.fields]}


@router.get('/config')
def config():
    return {'demo_mode': settings.demo_mode and settings.app_env != 'production', 'auth_provider': 'supabase' if settings.supabase_url else 'demo', 'max_upload_mb': settings.max_upload_mb, 'max_pdf_pages': settings.max_pdf_pages, 'llm_enabled': bool(settings.llm_api_key)}


@router.post('/auth/demo', status_code=201)
def demo(body: DemoInput, db: Session = Depends(get_db)):
    if not settings.demo_mode or settings.app_env == 'production':
        raise HTTPException(403, 'Demo mode is disabled')
    user, token = create_demo_session(db)
    seed_demo(db, user, body.scenario)
    return {'access_token': token, 'token_type': 'bearer', 'demo': True, 'scenario': body.scenario}


@router.get('/auth/me')
def me(user: User = Depends(current_user)):
    return {'id': user.id, 'email': user.email, 'demo': user.email.endswith('@example.invalid')}


@router.post('/auth/logout', status_code=204)
def logout(user: User = Depends(current_user), auth=Depends(bearer), db: Session = Depends(get_db)):
    session = db.get(DemoSession, hashlib.sha256(auth.credentials.encode()).hexdigest())
    if session:
        db.delete(session)
        db.commit()
    return Response(status_code=204)


@router.get('/demo/samples/{name}')
def get_sample(name: str):
    if not settings.demo_mode or settings.app_env == 'production' or name not in SAMPLES:
        raise HTTPException(404, 'Sample not found')
    return Response(sample_pdf(name), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="{name}"'})


@router.post('/profiles', status_code=201)
def create_profile(body: ProfileInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(TaxProfile).where(TaxProfile.user_id == user.id)):
        raise HTTPException(409, 'A profile already exists; update the current profile')
    profile = TaxProfile(user_id=user.id, financial_year=body.financial_year, answers_json=body.answers.model_dump())
    db.add(profile)
    record(db, user.id, 'profile_created', profile.id, None)
    db.commit()
    return profile_json(profile)


@router.get('/profiles/current')
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return profile_json(profile_for(db,user))


@router.put('/profiles/current')
def update_profile(body: ProfileInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    profile.financial_year = body.financial_year
    profile.answers_json = body.answers.model_dump()
    record(db, user.id, 'profile_updated', profile.id, None)
    db.commit()
    return profile_json(profile)


@router.post('/documents/upload', status_code=201)
def upload(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    name = mask_pan(safe_name(file.filename or 'document'))
    try:
        mime = validate_file(data,name)
    except ValueError as error:
        raise HTTPException(422, str(error))
    identifier = uid()
    suffix = {'application/pdf':'.pdf','image/jpeg':'.jpg','image/png':'.png'}[mime]
    key = f'{user.id}/documents/{identifier}{suffix}'
    storage.put(key,data,mime)
    doc = Document(id=identifier,user_id=user.id,profile_id=profile.id,filename=name,storage_path=key,file_hash=hashlib.sha256(data).hexdigest(),mime_type=mime)
    db.add(doc)
    record(db, user.id, 'document_uploaded', doc.id, None)
    db.commit()
    process_document(db,doc,data)
    return doc_json(doc)


@router.get('/documents')
def get_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [doc_json(doc) for doc in documents(db,profile_for(db,user))]


@router.get('/documents/{identifier}')
def get_document(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return doc_json(doc_for(db,user,identifier))


@router.get('/documents/{identifier}/preview')
def preview_document(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = doc_for(db,user,identifier)
    return Response(storage.read(doc.storage_path), media_type=doc.mime_type, headers={'Content-Disposition': 'inline; filename="source-document' + Path(doc.storage_path).suffix + '"', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "sandbox"})


@router.delete('/documents/{identifier}', status_code=204)
def remove_document(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = doc_for(db,user,identifier)
    storage.delete(doc.storage_path)
    db.delete(doc)
    record(db, user.id, 'document_deleted', doc.id, None)
    db.commit()
    return Response(status_code=204)


@router.post('/documents/{identifier}/process')
def reprocess(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = doc_for(db,user,identifier)
    process_document(db,doc,storage.read(doc.storage_path))
    record(db, user.id, 'document_reprocessed', doc.id)
    db.commit()
    return doc_json(doc)


@router.patch('/documents/{identifier}/verify')
def verify(identifier: str, body: VerifyInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = doc_for(db,user,identifier)
    available = {f.id:f for f in doc.fields}
    updates = []
    for entry in body.fields:
        if entry.id not in available:
            raise HTTPException(422, 'Field does not belong to this document')
        field = available[entry.id]
        try:
            # The masked PAN may be confirmed without sending the full identifier back.
            normalized = field.normalized_value if field.field_name == 'pan' and '*' in entry.value else normalize(field.field_name,entry.value)
        except ValueError as error:
            raise HTTPException(422,str(error))
        updates.append((field,normalized,entry.verified))
    for field,value,verified in updates:
        if value != field.normalized_value:
            field.extraction_method = 'user_corrected'
            field.review_indicator = 'Corrected by user; original evidence retained'
        field.normalized_value = value
        field.amount = Decimal(value) if field.field_name in MONEY_FIELDS else None
        field.verification_status = 'verified' if verified else 'unverified'
    if body.document_type:
        doc.document_type = body.document_type
    if doc.processing_status != 'extraction_failed':
        doc.processing_status = 'verified' if document_verified(doc) else 'needs_verification'
    record(db, user.id, 'fields_reviewed', doc.id, {'fields': [f.field_name for f, _, _ in updates], 'verified_count': sum(v for _, _, v in updates)})
    db.commit()
    return doc_json(doc)


@router.get('/checklist')
@router.post('/checklist/generate')
def checklist(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return summarize(db,profile_for(db,user))['checklist']


@router.get('/validation/issues')
@router.post('/validation/run')
def validation(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return summarize(db,profile_for(db,user))['issues']


@router.patch('/validation/issues/{identifier}')
def update_issue(identifier: str, body: IssueUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    summarize(db,profile)
    issue = db.scalar(select(ValidationIssue).where(ValidationIssue.id == identifier, ValidationIssue.profile_id == profile.id))
    if not issue:
        raise HTTPException(404, 'Issue not found; rerun validation')
    issue.status = body.status
    issue.resolution_note = body.resolution_note.strip()
    record(db, user.id, 'issue_updated', issue.id, {'status': body.status})
    db.commit()
    return serialize_issue(issue)


@router.get('/dashboard/summary')
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return summarize(db,profile_for(db,user))


@router.post('/assistant/chat')
def chat(body: ChatInput, user: User = Depends(current_user), db: Session = Depends(get_db), x_assistant_api_key: str | None = Header(default=None)):
    summary = summarize(db,profile_for(db,user))
    if body.provider == 'openai':
        if not body.share_context:
            raise HTTPException(400, 'Allow sharing your question and summarized financial context before using OpenAI.')
        return user_key_answer(body.message, summary, x_assistant_api_key, body.model)
    return answer(body.message, summary)


@router.post('/reports/generate', status_code=201)
def generate_report(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    summary = summarize(db,profile)
    data = make_pdf(summary,documents(db,profile))
    identifier = uid()
    key = f'{user.id}/reports/{identifier}.pdf'
    storage.put(key,data,'application/pdf')
    report = ReadinessReport(id=identifier,profile_id=profile.id,readiness_score=Decimal(summary['readiness_score']),report_path=key,snapshot_json=summary)
    db.add(report)
    record(db, user.id, 'report_generated', identifier, None)
    db.commit()
    return {'id':report.id,'readiness_score':str(report.readiness_score),'generated_at':report.generated_at.isoformat()}


@router.get('/reports')
def reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    return [{'id':r.id,'readiness_score':str(r.readiness_score),'generated_at':r.generated_at.isoformat(),'financial_year':r.snapshot_json['profile']['financial_year']} for r in db.scalars(select(ReadinessReport).where(ReadinessReport.profile_id == profile.id).order_by(ReadinessReport.generated_at.desc()))]


@router.get('/reports/{identifier}/download')
def download_report(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = profile_for(db,user)
    report = db.scalar(select(ReadinessReport).where(ReadinessReport.id == identifier,ReadinessReport.profile_id == profile.id))
    if not report:
        raise HTTPException(404,'Report not found')
    return Response(storage.read(report.report_path),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="TaxReady-readiness-report.pdf"','Cache-Control':'no-store'})

