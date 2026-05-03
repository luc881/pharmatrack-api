import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pharmatrack.db.session import Base, get_db
from pharmatrack.main import app
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(".env.test", override=True)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://luc:1278972@localhost/pharmatrack_test"
)

engine = create_engine(TEST_DATABASE_URL, pool_size=1, max_overflow=0)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# =========================================================
# 🔹 Sesión compartida entre fixtures y TestClient
# conftest.py la inyecta antes de cada test
# =========================================================
_current_session = None


def override_get_db():
    """
    Dependency override que devuelve SIEMPRE la misma sesión
    que los fixtures están usando. Así el TestClient ve los
    mismos datos que se crearon en los fixtures.
    """
    if _current_session is None:
        raise RuntimeError("db_session fixture not active")
    yield _current_session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, follow_redirects=True)


# =========================================================
# 🔹 Factory de rutas con prefijo /api/v1
# =========================================================
def route_client_factory(client, prefix: str = ""):
    base = f"/api/v1/{prefix.strip('/')}"

    def _url(path: str = "") -> str:
        clean = path.strip("/")
        if clean:
            return f"{base}/{clean}"
        return base

    def get(path: str = "", **kwargs):
        return client.get(_url(path), **kwargs)

    def post(path: str = "", **kwargs):
        return client.post(_url(path), **kwargs)

    def put(path: str = "", **kwargs):
        return client.put(_url(path), **kwargs)

    def patch(path: str = "", **kwargs):
        return client.patch(_url(path), **kwargs)

    def delete(path: str = "", **kwargs):
        return client.delete(_url(path), **kwargs)

    return get, post, put, patch, delete