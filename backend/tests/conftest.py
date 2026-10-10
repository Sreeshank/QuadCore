import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app, buckets
from app.db.session import Base, get_db
from app.core.config import settings

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_engine = create_engine('sqlite:///' + str(tmp_path/'test.db'),connect_args={'check_same_thread':False})
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(bind=test_engine,expire_on_commit=False)
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    monkeypatch.setattr(settings,'storage_dir',tmp_path/'private')
    monkeypatch.setattr(settings,'storage_backend','local')
    monkeypatch.setattr(settings,'demo_mode',True)
    monkeypatch.setattr(settings,'app_env','development')
    monkeypatch.setattr(settings,'llm_api_key','')
    monkeypatch.setattr(settings,'rate_limit',10000)
    buckets.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()

def login(client,scenario='blank'):
    response=client.post('/api/v1/auth/demo',json={'scenario':scenario})
    assert response.status_code==201,response.text
    return {'Authorization':'Bearer '+response.json()['access_token']}

def upload(client,headers,name='form16.pdf',data=None):
    from app.services.demo import sample_pdf
    response=client.post('/api/v1/documents/upload',headers=headers,files={'file':(name,data or sample_pdf(name),'application/pdf')})
    assert response.status_code==201,response.text
    return response.json()

def verify(client,headers,doc):
    response=client.patch('/api/v1/documents/'+doc['id']+'/verify',headers=headers,json={'fields':[{'id':f['id'],'value':f['value'],'verified':True} for f in doc['fields']]})
    assert response.status_code==200,response.text
    return response.json()

def profile(client,headers,**changes):
    from app.schemas import Answers
    answers=Answers(name='Ananya Demo').model_dump()
    answers.update(changes)
    response=client.post('/api/v1/profiles',headers=headers,json={'financial_year':'2025-26','answers':answers})
    assert response.status_code==201,response.text
    return response.json()

