from pharmatrack.api.routes.sale_batch_usage import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
sbu_get, *_ = route_client_factory(client, "sale-batch-usages")


# ==================================================================
# READ ALL
# ==================================================================
def test_read_all_sale_batch_usages(
    auth_headers,
    test_sale_detail,
    test_product_batch,
    db_session,
):
    # Generar al menos un SaleBatchUsage completando la venta
    from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
    allocate_batches_for_sale_detail(db_session, test_sale_detail)
    db_session.commit()

    response = sbu_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_read_all_sale_batch_usages_no_auth():
    response = sbu_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# READ BY ID
# ==================================================================
def test_read_sale_batch_usage_by_id(
    auth_headers,
    test_sale_detail,
    test_product_batch,
    db_session,
):
    from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
    from pharmatrack.models.sale_batch_usage.orm import SaleBatchUsage

    allocate_batches_for_sale_detail(db_session, test_sale_detail)
    db_session.commit()

    usage = db_session.query(SaleBatchUsage).first()
    assert usage is not None

    response = sbu_get(f"/{usage.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == usage.id
    assert data["sale_detail_id"] == usage.sale_detail_id
    assert data["batch_id"] == usage.batch_id
    assert data["quantity_used"] == usage.quantity_used
    assert "batch" in data
    assert "sale_detail" in data


def test_read_sale_batch_usage_not_found(auth_headers):
    response = sbu_get("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale batch usage not found"


def test_read_sale_batch_usage_by_id_no_auth(
    test_sale_detail,
    test_product_batch,
    db_session,
):
    from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
    from pharmatrack.models.sale_batch_usage.orm import SaleBatchUsage

    allocate_batches_for_sale_detail(db_session, test_sale_detail)
    db_session.commit()

    usage = db_session.query(SaleBatchUsage).first()
    assert usage is not None

    response = sbu_get(f"/{usage.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED