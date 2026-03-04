from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

Base = declarative_base()

_engine = None
_SessionLocal = None

def _get_engine():
    global _engine
    if _engine is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            from pharmatrack.config import settings
            database_url = settings.database_url
        _engine = create_engine(database_url)
    return _engine

def _get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal

def get_db() -> Session:
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()