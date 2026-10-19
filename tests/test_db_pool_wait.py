"""Pool lleno + rutas async: esperar conexión no debe congelar el event loop.

Con el pool de 1 conexión, la primera petición la tiene mientras hace await;
la segunda debe esperarla en el hilo de get_db. Si la espera ocurriera dentro
de la ruta, bloquearía el loop y la primera nunca la soltaría (timeout)."""
import asyncio

import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from pharmatrack.db import session as db_session_module
from pharmatrack.db.session import db_dependency

from .utils import TEST_DATABASE_URL


def test_segunda_peticion_espera_conexion_sin_congelar(monkeypatch):
    engine = create_engine(TEST_DATABASE_URL, pool_size=1, max_overflow=0, pool_timeout=3)
    monkeypatch.setattr(db_session_module, "_SessionLocal", sessionmaker(bind=engine))

    app = FastAPI()

    @app.get("/x")
    async def x(db: db_dependency):
        db.execute(text("select 1"))
        await asyncio.sleep(0.3)  # cede el loop con la conexión tomada
        return {"ok": True}

    async def two_at_once():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
            return await asyncio.gather(client.get("/x"), client.get("/x"))

    try:
        responses = asyncio.run(two_at_once())
    finally:
        engine.dispose()
    assert [r.status_code for r in responses] == [200, 200]
