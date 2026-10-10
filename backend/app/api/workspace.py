import csv
import io
import json
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
import pymupdf
from app.core.auth import current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import User, TaxProfile, Document, ExtractedField, ChecklistItem, ValidationIssue, ReadinessReport, AuditEvent
from app.schemas import ManualFieldInput, DeleteDataInput, BulkDeleteInput, normalize, MONEY_FIELDS
from app.services import storage
from app.services.audit import record
from app.services.rules import summarize, document_verified
from app.api.routes import doc_for, doc_json, profile_for, mask_pan

router = APIRouter(prefix='/api/v1')


@router.post('/documents/{identifier}/fields', status_code=201)
def add_field(identifier: str, body: ManualFieldInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = doc_for(db, user, identifier)
    if any(f.field_name == body.field_name for f in doc.fields):
        raise HTTPException(409, 'This field already exists. Edit it in the review form.')
    data = storage.read(doc.storage_path)
    pages = 1
    if doc.mime_type == 'application/pdf':
        with pymupdf.open(stream=data, filetype='pdf') as pdf:
            pages = len(pdf)
    if body.source_page > pages:
        raise HTTPException(422, f'This document contains only {pages} page(s)')
    value = normalize(body.field_name, body.value)
    field = ExtractedField(field_name=body.field_name, field_value=body.value,
        normalized_value=value, amount=Decimal(value) if body.field_name in MONEY_FIELDS else None,
        source_page=body.source_page, extraction_method='user_transcribed',
        verification_status='unverified', evidence=body.evidence.strip(),
        review_indicator='User-entered source transcription; requires confirmation')
    doc.fields.append(field)
    doc.processing_status = 'needs_verification'
    # Retain any extraction error so users know why they are entering fields manually.
    record(db, user.id, 'field_added', doc.id, {'field': body.field_name, 'source_page': body.source_page})
    db.commit()
    return doc_json(doc)


@router.delete('/documents/{identifier}/fields/{field_id}', status_code=204)
def delete_field(identifier: str, field_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = doc_for(db, user, identifier)
    field = next((f for f in doc.fields if f.id == field_id), None)
    if not field:
        raise HTTPException(404, 'Field not found')
    record(db, user.id, 'field_removed', doc.id, {'field': field.field_name})
    doc.fields.remove(field)
    doc.processing_status = 'verified' if document_verified(doc) else 'needs_verification'
    db.commit()
    return Response(status_code=204)


@router.post('/documents/bulk-delete', status_code=204)
def bulk_delete(body: BulkDeleteInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Resolve every owner before any file is removed; foreign IDs cannot produce partial deletion.
    docs = [doc_for(db, user, identifier) for identifier in dict.fromkeys(body.document_ids)]
    for doc in docs:
        storage.delete(doc.storage_path)
        record(db, user.id, 'document_deleted', doc.id, {'bulk': True})
        db.delete(doc)
    db.commit()
    return Response(status_code=204)


def owned_report(db, user, identifier):
    report = db.scalar(select(ReadinessReport).join(TaxProfile).where(ReadinessReport.id == identifier, TaxProfile.user_id == user.id))
    if not report:
        raise HTTPException(404, 'Report not found')
    return report


@router.get('/reports/{identifier}/snapshot')
def report_snapshot(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    report = owned_report(db, user, identifier)
    return {'id': report.id, 'generated_at': report.generated_at.isoformat(), 'summary': report.snapshot_json}


@router.delete('/reports/{identifier}', status_code=204)
def delete_report(identifier: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    report = owned_report(db, user, identifier)
    storage.delete(report.report_path)
    record(db, user.id, 'report_deleted', report.id)
    db.delete(report)
    db.commit()
    return Response(status_code=204)


@router.get('/account/activity')
def activity(user: User = Depends(current_user), db: Session = Depends(get_db)):
    events = db.scalars(select(AuditEvent).where(AuditEvent.user_id == user.id).order_by(AuditEvent.created_at.desc()).limit(200))
    return [{'id': e.id, 'action': e.action, 'resource_id': e.resource_id, 'details': e.details_json, 'created_at': e.created_at.isoformat()} for e in events]


@router.get('/account/export')
def export_workspace(user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(TaxProfile).where(TaxProfile.user_id == user.id))
    data = {'format_version': 1, 'account': {'id': user.id, 'email': user.email},
        'summary': summarize(db, profile) if profile else None,
        'documents': [doc_json(d) for d in db.scalars(select(Document).where(Document.user_id == user.id))],
        'reports': [{'id': r.id, 'generated_at': r.generated_at.isoformat(), 'summary': r.snapshot_json}
            for r in db.scalars(select(ReadinessReport).join(TaxProfile).where(TaxProfile.user_id == user.id))]}
    record(db, user.id, 'workspace_exported', details={'format': 'json'})
    db.commit()
    return Response(json.dumps(data, ensure_ascii=False, indent=2), media_type='application/json',
        headers={'Content-Disposition': 'attachment; filename="TaxReady-workspace.json"', 'Cache-Control': 'no-store'})


@router.get('/account/fields.csv')
def export_csv(user: User = Depends(current_user), db: Session = Depends(get_db)):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['document','category','field','value','verification','source_page','method'])
    def safe(value):
        text = str(value or '')
        return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')) else text
    for doc in db.scalars(select(Document).where(Document.user_id == user.id)):
        for field in doc.fields:
            writer.writerow([safe(v) for v in [mask_pan(doc.filename), doc.document_type, field.field_name,
                mask_pan(field.normalized_value), field.verification_status, field.source_page, field.extraction_method]])
    record(db, user.id, 'workspace_exported', details={'format': 'csv'})
    db.commit()
    return Response('\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="TaxReady-fields.csv"', 'Cache-Control': 'no-store'})


@router.delete('/account/data', status_code=204)
def delete_workspace(body: DeleteDataInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(TaxProfile).where(TaxProfile.user_id == user.id))
    if profile:
        reports = list(db.scalars(select(ReadinessReport).where(ReadinessReport.profile_id == profile.id)))
        docs = list(db.scalars(select(Document).where(Document.user_id == user.id)))
        for item in reports:
            storage.delete(item.report_path)
        for item in docs:
            storage.delete(item.storage_path)
        for model in (ChecklistItem, ValidationIssue, ReadinessReport):
            db.execute(delete(model).where(model.profile_id == profile.id))
        for doc in docs:
            db.delete(doc)
        db.flush()
        db.delete(profile)
    db.execute(delete(AuditEvent).where(AuditEvent.user_id == user.id))
    db.commit()
    return Response(status_code=204)

