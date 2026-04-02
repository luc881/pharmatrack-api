import pytest
from decimal import Decimal


# ------------------------------------------------------------------
# SaleDetail principal (test_sale + test_product, qty=3, discount=5)
# ------------------------------------------------------------------
@pytest.fixture
def test_sale_detail(db_session, test_sale, test_product):
    from pharmatrack.models.sale_details.orm import SaleDetail
    from pharmatrack.utils.sales_calculations import recalc_sale_totals

    quantity = Decimal("3")
    price_unit = Decimal(str(test_product.price_retail))
    discount = Decimal("5")

    tax = Decimal("0")
    if test_product.tax_percentage:
        tax = (
            (price_unit * quantity - discount)
            * Decimal(str(test_product.tax_percentage))
            / Decimal("100")
        )

    total = (price_unit * quantity) - discount + tax

    detail = SaleDetail(
        sale_id=test_sale.id,
        product_id=test_product.id,
        quantity=quantity,
        price_unit=price_unit,
        discount=discount,
        tax=tax,
        total=total,
        description="Detalle de venta de producto A",
    )
    db_session.add(detail)
    db_session.flush()
    recalc_sale_totals(db_session, test_sale)
    db_session.commit()
    db_session.refresh(detail)
    return detail


# ------------------------------------------------------------------
# SaleDetail secundario (test_sale + another_product, qty=2)
# ------------------------------------------------------------------
@pytest.fixture
def another_test_sale_detail(db_session, test_sale, another_product):
    from pharmatrack.models.sale_details.orm import SaleDetail
    from pharmatrack.utils.sales_calculations import recalc_sale_totals

    quantity = Decimal("2")
    price_unit = Decimal(str(another_product.price_retail))
    discount = Decimal("0")

    tax = Decimal("0")
    if another_product.tax_percentage:
        tax = (
            (price_unit * quantity)
            * Decimal(str(another_product.tax_percentage))
            / Decimal("100")
        )

    total = (price_unit * quantity) + tax

    detail = SaleDetail(
        sale_id=test_sale.id,
        product_id=another_product.id,
        quantity=quantity,
        price_unit=price_unit,
        discount=discount,
        tax=tax,
        total=total,
        description="Detalle de venta de producto B",
    )
    db_session.add(detail)
    db_session.flush()
    recalc_sale_totals(db_session, test_sale)
    db_session.commit()
    db_session.refresh(detail)
    return detail


# ------------------------------------------------------------------
# SaleDetail vinculado a una venta ya completada
# ------------------------------------------------------------------
@pytest.fixture
def sale_detail_completed_sale(db_session, completed_sale, test_product):
    from pharmatrack.models.sale_details.orm import SaleDetail
    from pharmatrack.utils.sales_calculations import recalc_sale_totals

    quantity = Decimal("1")
    price_unit = Decimal(str(test_product.price_retail))
    discount = Decimal("0")

    tax = Decimal("0")
    if test_product.tax_percentage:
        tax = (
            price_unit
            * Decimal(str(test_product.tax_percentage))
            / Decimal("100")
        )

    total = price_unit + tax

    detail = SaleDetail(
        sale_id=completed_sale.id,
        product_id=test_product.id,
        quantity=quantity,
        price_unit=price_unit,
        discount=discount,
        tax=tax,
        total=total,
    )
    db_session.add(detail)
    db_session.flush()
    recalc_sale_totals(db_session, completed_sale)
    db_session.commit()
    db_session.refresh(detail)
    return detail