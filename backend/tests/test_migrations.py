from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine,inspect
from app.core.config import settings

def test_frozen_migration_upgrade_and_downgrade(tmp_path,monkeypatch):
    url='sqlite:///' + str(tmp_path/'migration.db')
    monkeypatch.setattr(settings,'database_url',url)
    config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
    command.upgrade(config,'head')
    engine=create_engine(url)
    assert {'users','demo_sessions','tax_profiles','documents','extracted_fields','checklist_items','validation_issues','readiness_reports'} <= set(inspect(engine).get_table_names())
    assert any(i['name']=='ix_documents_file_hash' for i in inspect(engine).get_indexes('documents'))
    command.downgrade(config,'base')
    assert set(inspect(engine).get_table_names())=={'alembic_version'}
    engine.dispose()

