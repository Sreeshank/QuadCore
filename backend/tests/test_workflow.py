from decimal import Decimal
import io
import pytest
import pymupdf
from PIL import Image
from conftest import login,profile,upload,verify
from app.services.demo import sample_pdf
from app.core.config import settings
from app.services import extraction

def summary(client,h):
    response=client.get('/api/v1/dashboard/summary',headers=h)
    assert response.status_code==200,response.text
    return response.json()

def test_complete_acceptance_workflow_and_report(client,tmp_path):
    h=login(client)
    profile(client,h)
    docs=[upload(client,h,name) for name in ['form16.pdf','form26as.pdf','bank-interest.pdf']]
    assert [d['document_type'] for d in docs]==['form16','form26as','bank_interest']
    assert all(d['processing_status']=='needs_verification' for d in docs)
    assert docs[0]['fields'][0]['source_document_id']==docs[0]['id']
    assert not any('ABCDE1234F' in f['value'] or 'ABCDE1234F' in f['evidence'] for f in docs[0]['fields'])
    before=summary(client,h)
    assert before['verified_records']==0
    assert before['readiness_score']=='10.0'
    for doc in docs:verify(client,h,doc)
    s=summary(client,h)
    assert s['verified_records']==3
    assert s['missing_documents']==2
    assert s['readiness_score']=='59.0'
    assert s['components']['document_completeness']['score']=='60.0'
    assert s['components']['field_verification']['score']=='100.0'
    difference=[i for i in s['issues'] if i['issue_type']=='tds_difference']
    assert len(difference)==1
    assert difference[0]['details']['difference']=='3000.00'
    assert difference[0]['details']['value_a']=='45000.00'
    assert s['high_severity_issues']==1
    assert s['income_summary'][0]['amount']=='850000.00'
    assert s['income_summary'][1]['amount']=='12500.00'
    chat=client.post('/api/v1/assistant/chat',headers=h,json={'message':'Why does my TDS not match?'}).json()
    assert '3000.00' in chat['answer']
    assert {r['document_id'] for r in chat['references']}=={docs[0]['id'],docs[1]['id']}
    report=client.post('/api/v1/reports/generate',headers=h)
    assert report.status_code==201,report.text
    assert report.json()['readiness_score']==s['readiness_score']
    downloaded=client.get('/api/v1/reports/'+report.json()['id']+'/download',headers=h)
    assert downloaded.status_code==200
    pdf=pymupdf.open(stream=downloaded.content,filetype='pdf')
    text='\n'.join(p.get_text() for p in pdf)
    assert '59.0%' in text and '3000.00' in text
    assert '850,000.00' in text and '12,500.00' in text
    assert 'ABCDE1234F' not in text
    assert len(pdf)>=2
    (tmp_path/'readiness-report.pdf').write_bytes(downloaded.content)

def test_completed_and_incomplete_demo_profiles(client):
    complete=summary(client,login(client,'complete'))
    assert complete['readiness_score']=='100.0'
    assert complete['checklist_complete']==complete['checklist_total']==5
    assert complete['comparable_checks']==complete['passed_checks']==2
    assert complete['issues']==[]
    incomplete=summary(client,login(client,'incomplete'))
    assert incomplete['readiness_score']=='0.0'
    assert incomplete['missing_documents']==5

def test_checklist_personalization_and_no_applicable_items(client):
    h=login(client)
    profile(client,h,salary=False,bank_interest=False,employers=0)
    s=summary(client,h)
    assert s['checklist_total']==0
    assert s['readiness_score']=='100.0'
    assert all(i['status']=='not_applicable' for i in s['checklist'])
    p=s['profile']
    p['answers'].update({'capital_gains':True,'deductions':True})
    client.put('/api/v1/profiles/current',headers=h,json={'financial_year':p['financial_year'],'answers':p['answers']})
    s=summary(client,h)
    assert s['checklist_total']==4
    assert any(i['requirement_key']=='capital_gains' and i['status']=='missing' for i in s['checklist'])
    assert s['components']['consistency']['score']=='0.0'

def test_multiple_employers_do_not_count_duplicate_records(client):
    h=login(client);profile(client,h,employers=2)
    data=sample_pdf('form16.pdf')
    verify(client,h,upload(client,h,'form16.pdf',data))
    verify(client,h,upload(client,h,'form16.pdf',data))
    s=summary(client,h)
    item=next(i for i in s['checklist'] if i['requirement_key']=='form16')
    assert item['status']=='needs_review'
    assert '1 of 2' in item['description']
    assert s['income_summary'][0]['amount']=='850000.00'
    assert any(i['issue_type']=='duplicate' for i in s['issues'])

def test_wrong_year_and_noncomparable_context(client):
    h=login(client,'sample')
    docs=client.get('/api/v1/documents',headers=h).json()
    d=next(d for d in docs if d['document_type']=='form26as')
    year=next(f for f in d['fields'] if f['field_name']=='financial_year')
    client.patch('/api/v1/documents/'+d['id']+'/verify',headers=h,json={'fields':[{'id':year['id'],'value':'2024-25','verified':True}]})
    s=summary(client,h)
    assert any(i['issue_type']=='financial_year' for i in s['issues'])
    assert any(i['issue_type']=='not_comparable' for i in s['issues'])
    assert not any(i['issue_type']=='tds_difference' for i in s['issues'])
    assert s['comparable_checks']==0

def test_issue_resolution_requires_note_and_persists_until_values_change(client):
    h=login(client,'sample')
    issue=next(i for i in summary(client,h)['issues'] if i['issue_type']=='tds_difference')
    path='/api/v1/validation/issues/'+issue['id']
    assert client.patch(path,headers=h,json={'status':'resolved','resolution_note':'ok'}).status_code==422
    assert client.patch(path,headers=h,json={'status':'resolved','resolution_note':'Reviewed with employer; correction pending in statement.'}).status_code==200
    s=summary(client,h)
    assert next(i for i in s['issues'] if i['id']==issue['id'])['status']=='resolved'
    assert s['components']['consistency']['score']=='100.0'
    doc=next(d for d in client.get('/api/v1/documents',headers=h).json() if d['document_type']=='form16')
    tds=next(f for f in doc['fields'] if f['field_name']=='tds')
    client.patch('/api/v1/documents/'+doc['id']+'/verify',headers=h,json={'fields':[{'id':tds['id'],'value':'46000.00'}]})
    s=summary(client,h)
    new=next(i for i in s['issues'] if i['issue_type']=='tds_difference')
    assert new['id']!=issue['id'] and new['status']=='open' and new['details']['difference']=='4000.00'

def test_reprocess_clears_user_verification_and_deletion_recalculates(client):
    h=login(client);profile(client,h)
    d=verify(client,h,upload(client,h))
    assert d['processing_status']=='verified'
    r=client.post('/api/v1/documents/'+d['id']+'/process',headers=h)
    assert all(f['verification_status']=='unverified' for f in r.json()['fields'])
    assert client.delete('/api/v1/documents/'+d['id'],headers=h).status_code==204
    assert client.get('/api/v1/documents/'+d['id']+'/preview',headers=h).status_code==404
    assert summary(client,h)['documents_uploaded']==0

def test_failed_ocr_is_visible_and_reprocessable(client,monkeypatch):
    h=login(client);profile(client,h)
    def fail(*a):raise ValueError('OCR requires Tesseract.')
    monkeypatch.setattr(extraction,'ocr',fail)
    image=io.BytesIO();Image.new('RGB',(500,100),'white').save(image,'PNG')
    d=upload(client,h,'scan.png',image.getvalue())
    assert d['processing_status']=='extraction_failed' and 'Tesseract' in d['error_message']
    monkeypatch.setattr(extraction,'ocr',lambda *a:'FORM 16\nFinancial Year: 2025-26\nTDS: 1.00')
    r=client.post('/api/v1/documents/'+d['id']+'/process',headers=h)
    assert r.json()['processing_status']=='needs_verification'
    assert any(i['issue_type']=='missing_fields' for i in summary(client,h)['issues'])

def test_decimal_cents_comparison(client):
    h=login(client,'sample')
    docs=client.get('/api/v1/documents',headers=h).json()
    for kind,amount in [('form16','42000.10'),('form26as','42000.09')]:
        d=next(d for d in docs if d['document_type']==kind)
        f=next(f for f in d['fields'] if f['field_name']=='tds')
        assert client.patch('/api/v1/documents/'+d['id']+'/verify',headers=h,json={'fields':[{'id':f['id'],'value':amount}]}).status_code==200
    issue=next(i for i in summary(client,h)['issues'] if i['issue_type']=='tds_difference')
    assert issue['details']['difference']=='0.01'

def test_tax_law_questions_redirect_to_official_guidance(client):
    h=login(client,'sample')
    answer=client.post('/api/v1/assistant/chat',headers=h,json={'message':'What tax rate applies to me?'}).json()
    assert 'https://www.incometax.gov.in/' in answer['answer']


def test_ambiguous_annual_totals_are_review_only(client):
    h=login(client,'sample')
    original=sample_pdf('form16.pdf')
    pdf=pymupdf.open(stream=original,filetype='pdf')
    pages=[p.get_text() for p in pdf]
    from reportlab.pdfgen import canvas
    output=io.BytesIO();writer=canvas.Canvas(output)
    for index,line in enumerate(pages[0].replace('45,000.00','46,000.00').splitlines()):
        writer.drawString(30,800-index*20,line)
    writer.save()
    upload(client,h,'additional-form16.pdf',output.getvalue())
    s=summary(client,h)
    assert any(i['issue_type']=='not_comparable' for i in s['issues'])
    assert not any(i['issue_type']=='tds_difference' for i in s['issues'])

