from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

Base = declarative_base()

def _get_engine():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        from pharmatrack.config import settings
        database_url = settings.database_url
    return create_engine(database_url)

engine = _get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()