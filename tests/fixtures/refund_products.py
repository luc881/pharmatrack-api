import pytest


@pytest.fixture
def test_refund_product(
    db_session,
    test_product,
    test_sale_detail,
    test_product_batch,
    test_user_with_role_permissions_branch_auth,
):
    """
    Crea un RefundProduct NO reintegrable directamente en DB,
    sin pasar por el route ni tocar el stock.
    Útil para tests de READ, UPDATE y DELETE sin efectos secundarios.

    IMPORTANTE: test_product_batch debe declararse aunque no se use
    explícitamente — garantiza que el lote exista en DB antes de que
    test_sale_detail intente referenciar batch_usages.
    """
    from pharmatrack.models.refund_products.orm import RefundProduct

    refund = RefundProduct(
        product_id=test_product.id,
        quantity=1,
        sale_detail_id=test_sale_detail.id,
        user_id=test_user_with_role_permissions_branch_auth.id,
        is_reintegrable=False,   # False → no toca stock al crear/borrar por fixture
        reintegrated_batches={},
    )
    db_session.add(refund)
    db_session.commit()
    db_session.refresh(refund)
    return refund


@pytest.fixture
def completed_sale_detail(
    db_session,
    test_sale,
    test_sale_detail,
    test_product_batch,
):
    """
    Ejecuta allocate_batches sobre test_sale_detail y completa la venta,
    dejando SaleBatchUsage reales en DB.
    Necesario para tests de reintegro de stock.
    """
    from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
    from pharmatrack.utils.sales_calculations import recalc_sale_totals

    allocate_batches_for_sale_detail(db_session, test_sale_detail)
    recalc_sale_totals(db_session, test_sale)
    test_sale.status = "completed"
    db_session.commit()
    db_session.refresh(test_sale_detail)
    return test_sale_detail