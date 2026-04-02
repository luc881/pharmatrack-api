import pytest
from datetime import date


@pytest.fixture
def test_product_batch(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="LOT123456",
        expiration_date=date(2026, 12, 31),
        quantity=100,
        purchase_price=5.50,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def another_product_batch(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="LOT654321",
        expiration_date=date(2026, 6, 30),
        quantity=50,
        purchase_price=6.00,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def product_batch_with_stock(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="L001",
        expiration_date=date(2026, 12, 31),
        quantity=100,
        purchase_price=10.0,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def product_batch_with_low_stock(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="L002",
        expiration_date=date(2026, 12, 31),
        quantity=1,
        purchase_price=10.0,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch