import pytest


@pytest.fixture
def test_purchase(db_session, test_supplier, test_user_with_role_permissions_branch_auth):
    from pharmatrack.models.purchases.orm import Purchase

    purchase = Purchase(
        supplier_id=test_supplier.id,
        user_id=test_user_with_role_permissions_branch_auth.id,
        total=1180.00,
        description="Compra de medicamentos general",
    )
    db_session.add(purchase)
    db_session.commit()
    db_session.refresh(purchase)
    return purchase


@pytest.fixture
def another_purchase(db_session, test_supplier, test_user_with_role_permissions_branch_auth):
    from pharmatrack.models.purchases.orm import Purchase

    purchase = Purchase(
        supplier_id=test_supplier.id,
        user_id=test_user_with_role_permissions_branch_auth.id,
        total=500.00,
        description="Segunda compra de prueba",
    )
    db_session.add(purchase)
    db_session.commit()
    db_session.refresh(purchase)
    return purchase