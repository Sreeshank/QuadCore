from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

settings.storage_dir.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.database_url, connect_args={'check_same_thread': False} if settings.database_url.startswith('sqlite') else {}, pool_pre_ping=True)
if settings.database_url.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def set_sqlite_pragma(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
