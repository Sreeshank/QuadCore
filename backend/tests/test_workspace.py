import csv
import io
import json
import pytest
from conftest import login, profile, upload, verify
from app.core.config import settings

def setup(client):
    h=login(client);profile(client,h);return h,upload(client,h)

def test_manual_field_lifecycle_and_source_validation(client):
    h,d=setup(client); url='/api/v1/documents/'+d['id']
    original=next(f for f in d['fields'] if f['field_name']=='deductions')
    assert client.delete(url+'/fields/'+original['id'],headers=h).status_code==204
    body={'field_name':'deductions','value':'1234.50','source_page':2,'evidence':'Deductions 1234.50'}
    assert client.post(url+'/fields',headers=h,json=body).status_code==422
    body['source_page']=1
    r=client.post(url+'/fields',headers=h,json=body)
    assert r.status_code==201,r.text
    field=next(f for f in r.json()['fields'] if f['field_name']=='deductions')
    assert field['verification_status']=='unverified'
    assert field['extraction_method']=='user_transcribed'
    assert field['value']=='1234.50'
    assert client.post(url+'/fields',headers=h,json=body).status_code==409
    reviewed=verify(client,h,r.json())
    assert reviewed['processing_status']=='verified'
    r=client.patch(url+'/verify',headers=h,json={'fields':[{'id':field['id'],'value':'1234.50','verified':False}]})
    assert r.json()['processing_status']=='needs_verification'
    assert client.delete(url+'/fields/'+field['id'],headers=h).status_code==204
    assert all(f['id']!=field['id'] for f in client.get(url,headers=h).json()['fields'])

@pytest.mark.parametrize('name,value',[('fake_field','123'),('deductions','NaN'),('deductions','-1'),('deductions','1.234'),('financial_year','2025-29')])
def test_manual_field_invalid_inputs(client,name,value):
    h,d=setup(client)
    assert client.post('/api/v1/documents/'+d['id']+'/fields',headers=h,json={'field_name':name,'value':value,'source_page':1,'evidence':'source evidence'}).status_code==422

def test_cross_account_manual_bulk_and_reports(client):
    h,d=setup(client);other,foreign=setup(client)
    field=foreign['fields'][0]
    assert client.delete('/api/v1/documents/'+foreign['id']+'/fields/'+field['id'],headers=h).status_code==404
    assert client.post('/api/v1/documents/'+foreign['id']+'/fields',headers=h,json={'field_name':'deductions','value':'1','source_page':1,'evidence':'Deductions 1'}).status_code==404
    assert client.post('/api/v1/documents/bulk-delete',headers=h,json={'document_ids':[d['id'],foreign['id']]}).status_code==404
    assert client.get('/api/v1/documents/'+d['id']+'/preview',headers=h).status_code==200
    report=client.post('/api/v1/reports/generate',headers=other).json()
    assert client.get('/api/v1/reports/'+report['id']+'/snapshot',headers=h).status_code==404
    assert client.delete('/api/v1/reports/'+report['id'],headers=h).status_code==404
    assert client.post('/api/v1/documents/bulk-delete',headers=h,json={'document_ids':[d['id'],d['id']]}).status_code==204
    assert client.get('/api/v1/documents/'+foreign['id']+'/preview',headers=other).status_code==200

def test_saved_snapshot_is_immutable_and_report_deletable(client):
    h,d=setup(client)
    report=client.post('/api/v1/reports/generate',headers=h).json()
    url='/api/v1/reports/'+report['id']
    initial=client.get(url+'/snapshot',headers=h).json()
    assert 'summary' in initial
    verify(client,h,d)
    assert client.get(url+'/snapshot',headers=h).json()==initial
    assert client.delete(url,headers=h).status_code==204
    assert client.get(url+'/download',headers=h).status_code==404
    assert client.get(url+'/snapshot',headers=h).status_code==404

def test_exports_are_masked_scoped_and_csv_safe(client):
    h,d=setup(client);other,foreign=setup(client)
    url='/api/v1/documents/'+d['id']
    field=next(f for f in d['fields'] if f['field_name']=='employer_name')
    assert client.patch(url+'/verify',headers=h,json={'fields':[{'id':field['id'],'value':'=HYPERLINK("bad")','verified':False}]}).status_code==200
    exported=client.get('/api/v1/account/export',headers=h)
    assert exported.status_code==200,exported.text
    data=exported.json()
    assert [x['id'] for x in data['documents']]==[d['id']]
    assert 'ABCDE1234F' not in exported.text
    csv_response=client.get('/api/v1/account/fields.csv',headers=h)
    rows=list(csv.DictReader(io.StringIO(csv_response.text.lstrip('\ufeff'))))
    assert next(r for r in rows if r['field']=='employer_name')['value'].startswith("'=")
    events=client.get('/api/v1/account/activity',headers=h).json()
    assert sum(e['action']=='workspace_exported' for e in events)==2
    assert foreign['id'] not in json.dumps(events)
    assert 'HYPERLINK' not in json.dumps(events)

def test_delete_workspace_requires_confirmation_and_isolates_accounts(client):
    h,d=setup(client);other,foreign=setup(client)
    report=client.post('/api/v1/reports/generate',headers=h).json()
    assert client.delete('/api/v1/account/data',headers=h).status_code==422
    assert client.request('DELETE','/api/v1/account/data',headers=h,json={'confirmation':'DELETE MY DATA'}).status_code==204
    assert client.get('/api/v1/profiles/current',headers=h).status_code==404
    assert client.get('/api/v1/account/activity',headers=h).json()==[]
    assert client.get('/api/v1/documents/'+d['id']+'/preview',headers=h).status_code==404
    assert client.get('/api/v1/reports/'+report['id']+'/download',headers=h).status_code==404
    assert client.get('/api/v1/documents/'+foreign['id']+'/preview',headers=other).status_code==200
    assert len(list(settings.storage_dir.rglob('*.pdf')))==1
    profile(client,h)
    assert client.get('/api/v1/account/export',headers=h).json()['documents']==[]

