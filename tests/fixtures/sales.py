import pytest
from datetime import date


# ------------------------------------------------------------------
# Venta vacía en draft (para tests de complete/empty)
# ------------------------------------------------------------------
@pytest.fixture
def empty_sale(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.sales.orm import Sale

    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id,
        status="draft",
        subtotal=0,
        tax=0,
        discount=0,
        total=0,
    )
    db_session.add(sale)
    db_session.commit()
    db_session.refresh(sale)
    return sale


# ------------------------------------------------------------------
# Venta en draft con totales (para tests de CRUD)
# ------------------------------------------------------------------
@pytest.fixture
def test_sale(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.sales.orm import Sale

    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id,
        subtotal=100,
        tax=16,
        discount=5,
        total=111,
        status="draft",
        description="Venta de medicamentos varios",
    )
    db_session.add(sale)
    db_session.commit()
    db_session.refresh(sale)
    return sale


# ------------------------------------------------------------------
# Segunda venta en draft
# ------------------------------------------------------------------
@pytest.fixture
def another_test_sale(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.sales.orm import Sale

    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id,
        subtotal=200,
        tax=32,
        discount=10,
        total=222,
        status="draft",
        description="Venta de productos varios",
    )
    db_session.add(sale)
    db_session.commit()
    db_session.refresh(sale)
    return sale


# ------------------------------------------------------------------
# Venta ya completada (para tests que validan restricciones)
# ------------------------------------------------------------------
@pytest.fixture
def completed_sale(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.sales.orm import Sale

    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id,
        status="completed",
        subtotal=100,
        tax=0,
        discount=0,
        total=100,
    )
    db_session.add(sale)
    db_session.commit()
    db_session.refresh(sale)
    return sale


# ------------------------------------------------------------------
# Venta cancelada
# ------------------------------------------------------------------
@pytest.fixture
def cancelled_sale(db_session, test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.sales.orm import Sale

    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id,
        status="cancelled",
        subtotal=50,
        tax=0,
        discount=0,
        total=50,
    )
    db_session.add(sale)
    db_session.commit()
    db_session.refresh(sale)
    return sale


# ------------------------------------------------------------------
# SaleDetail vinculado a test_sale + test_product (cantidad=2)
# Para tests de complete_sale con stock suficiente
# ------------------------------------------------------------------
@pytest.fixture
def test_sale_detail(db_session, test_sale, test_product):
    from pharmatrack.models.sale_details.orm import SaleDetail
    from decimal import Decimal

    detail = SaleDetail(
        sale_id=test_sale.id,
        product_id=test_product.id,
        quantity=Decimal("2"),
        price_unit=Decimal("50.00"),
        discount=Decimal("0"),
        tax=Decimal("0"),
        total=Decimal("100.00"),
    )
    db_session.add(detail)
    db_session.commit()
    db_session.refresh(detail)
    return detail


# ------------------------------------------------------------------
# ProductBatch con stock suficiente (quantity=50) para test_product
# ------------------------------------------------------------------
@pytest.fixture
def test_product_batch(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="LOT-TEST-001",
        expiration_date=date(2028, 12, 31),
        quantity=50,
        purchase_price=30.00,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


# ------------------------------------------------------------------
# ProductBatch con stock insuficiente (quantity=1, detail pide 2)
# ------------------------------------------------------------------
@pytest.fixture
def product_batch_with_low_stock(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="LOT-LOW-001",
        expiration_date=date(2028, 12, 31),
        quantity=1,
        purchase_price=30.00,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch