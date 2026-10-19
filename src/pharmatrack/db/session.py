from typing import Annotated

from fastapi import Depends
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

def SessionLocal() -> Session:
    return _get_session_local()()

def get_db() -> Session:
    db = _get_session_local()()
    try:
        # La conexión se toma aquí, en el hilo donde FastAPI corre esta
        # dependencia. Las rutas son async con SQLAlchemy síncrono: si la espera
        # del pool lleno pasara dentro de la ruta, congelaría el event loop y con
        # él a las peticiones que tienen las conexiones y las iban a soltar
        # (2026-10-19: un borrado masivo dejó el API colgado varios minutos).
        db.connection()
        yield db
    finally:
        db.close()


# Dependencia compartida por todos los routers
db_dependency = Annotated[Session, Depends(get_db)]