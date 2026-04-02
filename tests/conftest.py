import pytest
from sqlalchemy import text
from pharmatrack.db.session import Base
from . import utils
from .utils import engine, TestingSessionLocal

from .fixtures.users import *
from .fixtures.roles import *
from .fixtures.permissions import *
from .fixtures.branches import *
from .fixtures.products import *
from .fixtures.product_categories import *
from .fixtures.sales import *
from .fixtures.sale_payments import *
from .fixtures.sale_details import *
from .fixtures.refund_products import *
from .fixtures.suppliers import *
from .fixtures.purchases import *
from .fixtures.purchase_details import *
from .fixtures.product_batches import *
from .fixtures.product_master import *
from .fixtures.product_brand import *
from .fixtures.ingredients import *


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crea todas las tablas una vez al inicio de la sesión de tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    """
    Crea una sesión limpia para cada test e inyecta la misma sesión
    en utils._current_session para que el TestClient la comparta.
    """
    session = TestingSessionLocal()

    # Limpiar BD
    table_names = list(Base.metadata.tables.keys())
    tables_str = ", ".join(table_names)
    session.execute(text(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE;"))
    session.commit()

    # ✅ Compartir esta sesión con override_get_db
    utils._current_session = session

    yield session

    # Limpiar al terminar el test
    utils._current_session = None
    session.close()