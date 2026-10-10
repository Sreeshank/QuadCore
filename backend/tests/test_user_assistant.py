import json
import httpx
import pytest
from conftest import login
from app.services import user_assistant
KEY='sk-test-only-never-a-real-credential'

def request(client,headers,**changes):
    body={'message':'Why does my TDS differ?', 'provider':'openai','model':'gpt-4.1-mini','share_context':True}
    body.update(changes)
    return client.post('/api/v1/assistant/chat',headers={**headers,'X-Assistant-Api-Key':KEY},json=body)

def test_user_key_context_is_minimized_and_not_persisted(client,monkeypatch):
    h=login(client,'sample');seen={}
    def post(url,**kwargs):
        seen.update(url=url,**kwargs)
        return httpx.Response(200,json={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'Review the INR 3000.00 difference.'}]}]},request=httpx.Request('POST',url))
    monkeypatch.setattr(user_assistant.httpx,'post',post)
    r=request(client,h)
    assert r.status_code==200,r.text
    assert r.json()['mode']=='openai_user_key'
    assert len(r.json()['references'])==2
    assert seen['url']=='https://api.openai.com/v1/responses'
    assert seen['headers']['Authorization']=='Bearer '+KEY
    assert seen['json']['store'] is False
    sent=json.dumps(seen['json'])
    for excluded in ['Sammer','Ananya','ABCDE1234F','Example Technologies','example.invalid',KEY]:
        assert excluded not in sent
    assert '3000.00' in sent
    assert KEY not in client.get('/api/v1/account/export',headers=h).text
    assert KEY not in client.get('/api/v1/account/activity',headers=h).text

def test_builtin_does_not_call_provider_even_with_header(client,monkeypatch):
    monkeypatch.setattr(user_assistant.httpx,'post',lambda *a,**k:pytest.fail('Unexpected provider call'))
    h=login(client,'sample')
    assert request(client,h,provider='builtin').json()['mode']=='grounded_template'
    assert request(client,h,share_context=False).status_code==400
    r=client.post('/api/v1/assistant/chat',headers=h,json={'message':'hello','provider':'openai','share_context':True})
    assert r.status_code==400

@pytest.mark.parametrize('status,expected',[(401,400),(403,400),(429,429),(400,400),(404,400),(500,502),(302,502)])
def test_provider_errors_never_echo_secrets(client,monkeypatch,status,expected):
    def post(url,**kwargs):
        return httpx.Response(status,json={'error':KEY},request=httpx.Request('POST',url))
    monkeypatch.setattr(user_assistant.httpx,'post',post)
    r=request(client,login(client,'sample'))
    assert r.status_code==expected,r.text
    assert KEY not in r.text

def test_timeout_and_empty_response(client,monkeypatch):
    h=login(client,'sample')
    def timeout(*a,**kw):raise httpx.ReadTimeout(KEY)
    monkeypatch.setattr(user_assistant.httpx,'post',timeout)
    r=request(client,h);assert r.status_code==504;assert KEY not in r.text
    monkeypatch.setattr(user_assistant.httpx,'post',lambda url,**kw:httpx.Response(200,json={'status':'completed','output':[]},request=httpx.Request('POST',url)))
    assert request(client,h).status_code==502

def test_key_model_validation_and_cors(client,monkeypatch):
    monkeypatch.setattr(user_assistant.httpx,'post',lambda *a,**k:pytest.fail('Unexpected provider call'))
    h=login(client,'sample')
    assert request(client,h,model='https://localhost').status_code==422
    assert request(client,h,provider='unknown').status_code==422
    r=client.options('/api/v1/assistant/chat',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'X-Assistant-Api-Key'})
    assert r.status_code==200

