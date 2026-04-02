import pytest


@pytest.fixture
def test_supplier(db_session):
    from pharmatrack.models.suppliers.orm import Supplier

    supplier = Supplier(
        name="Distribuidora ABC S.A.",
        logo="https://example.com/logo.png",
        email="contacto@abc.com",
        phone="+52 555-123-4567",
        address="Av. Reforma 123, CDMX",
        rfc="ABC123456789",
        is_active=True,
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def another_supplier(db_session):
    from pharmatrack.models.suppliers.orm import Supplier

    supplier = Supplier(
        name="Otra Distribuidora S.A.",
        logo="https://example.com/logo2.png",
        email="contacto2@abc.com",
        phone="+52 555-987-6543",
        address="Calle Falsa 123, CDMX",
        rfc="DEF987654321",
        is_active=True,
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier