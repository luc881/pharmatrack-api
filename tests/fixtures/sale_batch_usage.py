import pytest


@pytest.fixture
def test_complete_sale_with_usage(
    db_session,
    test_sale,
    test_sale_detail,
    test_product_batch,
):
    """
    Completa test_sale ejecutando la lógica real de allocate_batches,
    dejando al menos un SaleBatchUsage en la base de datos.
    Depende de:
      - test_sale          (venta en draft)
      - test_sale_detail   (detalle con quantity=2, product=test_product)
      - test_product_batch (lote con quantity=50 del mismo product)
    """
    from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
    from pharmatrack.utils.sales_calculations import recalc_sale_totals

    allocate_batches_for_sale_detail(db_session, test_sale_detail)
    recalc_sale_totals(db_session, test_sale)
    test_sale.status = "completed"
    db_session.commit()
    db_session.refresh(test_sale)

    return test_sale