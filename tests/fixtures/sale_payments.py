import pytest


@pytest.fixture
def test_sale_payment(db_session, test_sale):
    from pharmatrack.models.sale_payments.orm import SalePayment

    payment = SalePayment(
        sale_id=test_sale.id,
        method_payment="card",
        transaction_number="TX123456789",
        bank="BBVA",
        amount=100.00,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def another_test_sale_payment(db_session, another_test_sale):
    from pharmatrack.models.sale_payments.orm import SalePayment

    payment = SalePayment(
        sale_id=another_test_sale.id,
        method_payment="cash",
        transaction_number=None,
        bank=None,
        amount=222.00,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment