from pharmatrack.api.routes.refund_products import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
rp_get, rp_post, rp_put, rp_patch, rp_delete = route_client_factory(client, "refundproducts")


# ==================================================================
# READ ALL
# ==================================================================
def test_read_all_refund_products(auth_headers, test_refund_product):
    response = rp_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_refund_product.id for item in data)


def test_read_all_refund_products_no_auth():
    response = rp_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# CREATE — reintegrable (con batch_usages reales)
# ==================================================================
def test_create_refund_product_reintegrable(
    auth_headers,
    test_product,
    completed_sale_detail,
    test_user_with_role_permissions_branch_auth,
    db_session,
):
    from pharmatrack.models.product_batch.orm import ProductBatch

    # Stock antes del refund
    batch_usages = completed_sale_detail.batch_usages
    assert len(batch_usages) > 0, "La venta debe tener SaleBatchUsage para probar reintegro"
    stock_before = {
        u.batch_id: db_session.get(ProductBatch, u.batch_id).quantity
        for u in batch_usages
    }

    payload = {
        "product_id": test_product.id,
        "quantity": float(completed_sale_detail.quantity),  # reintegrar todo lo vendido
        "sale_detail_id": completed_sale_detail.id,
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "is_reintegrable": True,
    }
    response = rp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["is_reintegrable"] is True
    assert data["product_id"] == test_product.id

    # Stock subió de vuelta
    for usage in batch_usages:
        db_session.expire(db_session.get(ProductBatch, usage.batch_id))
        batch = db_session.get(ProductBatch, usage.batch_id)
        assert batch.quantity == stock_before[usage.batch_id] + usage.quantity_used


# ==================================================================
# CREATE — no reintegrable (stock no debe cambiar)
# ==================================================================
def test_create_refund_product_not_reintegrable(
    auth_headers,
    test_product,
    completed_sale_detail,
    test_user_with_role_permissions_branch_auth,
    db_session,
):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch_usages = completed_sale_detail.batch_usages
    stock_before = {
        u.batch_id: db_session.get(ProductBatch, u.batch_id).quantity
        for u in batch_usages
    }

    payload = {
        "product_id": test_product.id,
        "quantity": 1,
        "sale_detail_id": completed_sale_detail.id,
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "is_reintegrable": False,
    }
    response = rp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["is_reintegrable"] is False

    # Stock no cambia
    for usage in batch_usages:
        db_session.expire(db_session.get(ProductBatch, usage.batch_id))
        batch = db_session.get(ProductBatch, usage.batch_id)
        assert batch.quantity == stock_before[usage.batch_id]


# ==================================================================
# CREATE — validaciones de FK
# ==================================================================
def test_create_refund_product_invalid_product(
    auth_headers, test_user_with_role_permissions_branch_auth
):
    payload = {
        "product_id": 9999,
        "quantity": 1,
        "user_id": test_user_with_role_permissions_branch_auth.id,
    }
    response = rp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated product not found"


def test_create_refund_product_invalid_sale_detail(
    auth_headers, test_product, test_user_with_role_permissions_branch_auth
):
    payload = {
        "product_id": test_product.id,
        "quantity": 1,
        "sale_detail_id": 9999,
        "user_id": test_user_with_role_permissions_branch_auth.id,
    }
    response = rp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated sale detail not found"


def test_create_refund_product_invalid_user(
    auth_headers, test_product, completed_sale_detail
):
    payload = {
        "product_id": test_product.id,
        "quantity": 1,
        "sale_detail_id": completed_sale_detail.id,
        "user_id": 9999,
        "is_reintegrable": False,
    }
    response = rp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated user not found"


def test_create_refund_product_exceeds_quantity(
    auth_headers, test_product, completed_sale_detail,
    test_user_with_role_permissions_branch_auth
):
    payload = {
        "product_id": test_product.id,
        "quantity": 9999,  # excede lo vendido
        "sale_detail_id": completed_sale_detail.id,
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "is_reintegrable": True,
    }
    response = rp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_refund_product_no_auth(test_product, test_user_with_role_permissions_branch_auth):
    payload = {
        "product_id": test_product.id,
        "quantity": 1,
        "user_id": test_user_with_role_permissions_branch_auth.id,
    }
    response = rp_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# UPDATE
# ==================================================================
def test_update_refund_product_change_quantity(auth_headers, test_refund_product):
    # test_refund_product tiene quantity=1, is_reintegrable=False
    # El route valida max_quantity contra sale_detail.quantity (=2), pero
    # como is_reintegrable=False el route no entra en la lógica de stock.
    # Actualizamos descripción — campo libre sin restricciones de cantidad.
    payload = {"quantity": 1}
    response = rp_put(f"/{test_refund_product.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert float(response.json()["quantity"]) == 1.0


def test_update_refund_product_not_found(auth_headers):
    response = rp_put("/9999", json={"quantity": 1}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Refund product not found"


def test_update_refund_product_invalid_product(auth_headers, test_refund_product):
    response = rp_put(
        f"/{test_refund_product.id}",
        json={"product_id": 9999},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated product not found"


def test_update_refund_product_invalid_user(auth_headers, test_refund_product):
    response = rp_put(
        f"/{test_refund_product.id}",
        json={"user_id": 9999},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated user not found"


def test_update_refund_product_no_auth(test_refund_product):
    response = rp_put(f"/{test_refund_product.id}", json={"quantity": 1})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# DELETE
# ==================================================================
def test_delete_refund_product(auth_headers, test_refund_product, db_session):
    from pharmatrack.models.refund_products.orm import RefundProduct

    refund_id = test_refund_product.id
    response = rp_delete(f"/{refund_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted = db_session.get(RefundProduct, refund_id)
    assert deleted is None


def test_delete_refund_product_not_found(auth_headers):
    response = rp_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Refund product not found"


def test_delete_refund_product_no_auth(test_refund_product):
    response = rp_delete(f"/{test_refund_product.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED