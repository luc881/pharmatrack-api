import pytest


@pytest.fixture
def test_purchase_detail(db_session, test_purchase, test_product):
    from pharmatrack.models.purchase_details.orm import PurchaseDetail
    from datetime import date

    detail = PurchaseDetail(
        purchase_id=test_purchase.id,
        product_id=test_product.id,
        quantity=10,
        unit_price=100.00,
        expiration_date=date(2027, 6, 30),
        lot_code="LOT-2025-001",
    )
    db_session.add(detail)
    db_session.commit()
    db_session.refresh(detail)
    return detail


@pytest.fixture
def another_purchase_detail(db_session, test_purchase, test_product):
    from pharmatrack.models.purchase_details.orm import PurchaseDetail
    from datetime import date

    detail = PurchaseDetail(
        purchase_id=test_purchase.id,
        product_id=test_product.id,
        quantity=5,
        unit_price=50.00,
        expiration_date=date(2027, 12, 31),
        lot_code="LOT-2025-002",
    )
    db_session.add(detail)
    db_session.commit()
    db_session.refresh(detail)
    return detail