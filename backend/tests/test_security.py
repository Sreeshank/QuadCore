import hashlib
from datetime import datetime,timedelta,timezone
import pytest
from conftest import login,profile,upload
from app.core.config import settings
from app.core.config import Settings
from app.services import storage
from app.models import DemoSession
from app.db.session import get_db
from app.main import app

@pytest.mark.parametrize('method,path,body',[('get','/documents',None),('get','/profiles/current',None),('get','/dashboard/summary',None),('get','/checklist',None),('post','/reports/generate',None),('post','/assistant/chat',{'message':'score'})])
def test_unauthorized_access(client,method,path,body):
    response=getattr(client,method)('/api/v1'+path,**({'json':body} if body else {}))
    assert response.status_code==401

def test_user_ownership_isolation(client):
    a=login(client,'sample');b=login(client);profile(client,b)
    doc=client.get('/api/v1/documents',headers=a).json()[0]
    for suffix in ['', '/preview']:
        assert client.get('/api/v1/documents/'+doc['id']+suffix,headers=b).status_code==404
    assert client.delete('/api/v1/documents/'+doc['id'],headers=b).status_code==404
    assert client.post('/api/v1/documents/'+doc['id']+'/process',headers=b).status_code==404
    assert client.patch('/api/v1/documents/'+doc['id']+'/verify',headers=b,json={'fields':[]}).status_code==404
    issue=client.get('/api/v1/validation/issues',headers=a).json()[0]
    assert client.patch('/api/v1/validation/issues/'+issue['id'],headers=b,json={'status':'under_review'}).status_code==404
    report=client.post('/api/v1/reports/generate',headers=a).json()
    assert client.get('/api/v1/reports/'+report['id']+'/download',headers=b).status_code==404
    assert client.get('/api/v1/documents',headers=b).json()==[]
    assert client.get('/api/v1/reports',headers=b).json()==[]

def test_field_ownership_and_atomic_validation(client):
    a=login(client,'sample')
    docs=client.get('/api/v1/documents',headers=a).json()
    first,second=docs[:2]
    assert client.patch('/api/v1/documents/'+first['id']+'/verify',headers=a,json={'fields':[{'id':second['fields'][0]['id'],'value':'123'}]}).status_code==422

def test_invalid_signature_unsafe_filename_private_storage(client):
    h=login(client);profile(client,h)
    response=client.post('/api/v1/documents/upload',headers=h,files={'file':('secret.pdf',b'not a PDF','application/pdf')})
    assert response.status_code==422
    from app.services.demo import sample_pdf
    d=upload(client,h,'../../form16.pdf',sample_pdf('form16.pdf'))
    assert d['filename']=='form16.pdf'
    assert 'storage_path' not in d
    assert client.get('/data/private/'+d['id']+'.pdf').status_code==404
    with pytest.raises(ValueError):
        storage.read('../../outside.txt')
    assert client.get('/api/v1/documents/'+d['id']+'/preview',headers=h).headers['cache-control']=='no-store'

def test_demo_disabled_in_production_and_invalid_tokens(client,monkeypatch):
    monkeypatch.setattr(settings,'app_env','production')
    assert client.post('/api/v1/auth/demo',json={'scenario':'blank'}).status_code==403
    assert client.get('/api/v1/demo/samples/form16.pdf').status_code==404
    assert client.get('/api/v1/auth/me',headers={'Authorization':'Bearer demo_invalid'}).status_code==401

def test_production_config_fails_closed():
    with pytest.raises(RuntimeError,match='DEMO_MODE'):
        Settings(app_env='production',demo_mode=True).validate_runtime()
    with pytest.raises(RuntimeError,match='authentication'):
        Settings(app_env='production',demo_mode=False,supabase_url='').validate_runtime()

def test_logout_invalidates_demo_token(client):
    h=login(client)
    assert client.post('/api/v1/auth/logout',headers=h).status_code==204
    assert client.get('/api/v1/auth/me',headers=h).status_code==401

def test_cors_and_rate_limit(client,monkeypatch):
    assert client.options('/api/v1/documents',headers={'Origin':'https://untrusted.example','Access-Control-Request-Method':'GET'}).status_code==400
    allowed=client.options('/api/v1/documents',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'GET'})
    assert allowed.headers['access-control-allow-origin']=='http://localhost:5173'
    monkeypatch.setattr(settings,'rate_limit',1)
    client.get('/api/v1/config')
    assert client.get('/api/v1/config').status_code==429

def test_request_size_limit(client,monkeypatch):
    h=login(client)
    r=client.post('/api/v1/assistant/chat',headers=h,content=b'x'*70000)
    assert r.status_code==413


def test_public_storage_bucket_rejected(monkeypatch):
    monkeypatch.setattr(settings,'storage_backend','supabase')
    monkeypatch.setattr(settings,'supabase_url','https://supabase.example')
    class Result:
        def raise_for_status(self):pass
        def json(self):return {'public':True}
    monkeypatch.setattr(storage.httpx,'get',lambda *a,**kw:Result())
    with pytest.raises(RuntimeError,match='private'):
        storage.ensure_private_bucket()
    monkeypatch.setattr(Result,'json',lambda self:{'public':False})
    storage.ensure_private_bucket()

