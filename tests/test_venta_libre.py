"""Venta libre: productos sin control de lotes (granel por peso).

tracks_batches=False → la venta se cobra sin validar ni descontar stock:
se pesa la pieza, se teclea la cantidad en gramos y se completa la venta
aunque el producto no tenga ningún lote.
"""
from decimal import Decimal

from fastapi import status

from pharmatrack.models.products.schemas import _product_slug

from .utils import client


def _granel_product(db_session, category_id):
    from pharmatrack.models.products.orm import Product

    product = Product(
        title="Corteza de encino (granel)",
        slug=_product_slug("Corteza de encino (granel)", "CORTEZA-T"),
        sku="CORTEZA-T",
        price_retail=0.06,
        price_cost=0.02,
        is_active=True,
        is_unit_sale=False,
        unit_name="g",
        tracks_batches=False,
        product_category_id=category_id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_venta_libre_completes_without_batches(
    auth_headers, db_session, test_product_category,
    test_user_with_role_permissions_branch_auth, test_branch,
):
    from pharmatrack.models.sales.orm import Sale
    from pharmatrack.models.sale_details.orm import SaleDetail
    from pharmatrack.models.sale_batch_usage.orm import SaleBatchUsage

    product = _granel_product(db_session, test_product_category.id)

    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id,
        status="draft", subtotal=0, tax=0, discount=0, total=0,
    )
    db_session.add(sale)
    db_session.commit()

    # 320 g pesados al momento — el producto NO tiene lotes
    detail = SaleDetail(
        sale_id=sale.id,
        product_id=product.id,
        quantity=Decimal("320"),
        price_unit=Decimal("0.06"),
        discount=Decimal("0"),
        tax=Decimal("0"),
        total=Decimal("19.20"),
    )
    db_session.add(detail)
    db_session.commit()

    response = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK, response.text

    # Sin trazabilidad de lotes: no hay nada que descontar
    usages = db_session.query(SaleBatchUsage).filter_by(sale_detail_id=detail.id).all()
    assert usages == []
