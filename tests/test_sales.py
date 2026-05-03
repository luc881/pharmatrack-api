from pharmatrack.api.routes.sales import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
sales_get, sales_post, sales_put, sales_patch, sales_delete = route_client_factory(client, "sales")


# ==================================================================
# READ ALL
# ==================================================================
def test_read_all_sales(auth_headers, test_sale):
    response = sales_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    # El endpoint devuelve paginado: {data: [...], total, page, ...}
    assert "data" in body
    data = body["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_sale.id for item in data)


def test_read_all_sales_no_auth():
    response = sales_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# CREATE
# ==================================================================
def test_create_sale_success(
    auth_headers,
    test_user_with_role_permissions_branch_auth,
    test_branch,
):
    payload = {
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "branch_id": test_branch.id,
        "description": "Venta de medicamentos varios",
    }
    response = sales_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["status"] == "draft"
    assert float(data["subtotal"]) == 0.0
    assert float(data["tax"]) == 0.0
    assert float(data["discount"]) == 0.0
    assert float(data["total"]) == 0.0
    assert data["user_id"] == payload["user_id"]
    assert data["branch_id"] == payload["branch_id"]
    assert "id" in data


def test_create_sale_missing_fields(auth_headers):
    # Falta user_id y branch_id
    payload = {"description": "Incompleta"}
    response = sales_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()


def test_create_sale_invalid_user(auth_headers, test_branch):
    payload = {
        "user_id": 9999,
        "branch_id": test_branch.id,
    }
    response = sales_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User ID does not exist."


def test_create_sale_invalid_branch(auth_headers, test_user_with_role_permissions_branch_auth):
    payload = {
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "branch_id": 9999,
    }
    response = sales_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Branch ID does not exist."


def test_create_sale_no_auth(test_user_with_role_permissions_branch_auth, test_branch):
    payload = {
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "branch_id": test_branch.id,
    }
    response = sales_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# UPDATE
# ==================================================================
def test_update_sale_partial(auth_headers, test_sale):
    payload = {
        "status": "cancelled",
        "description": "Venta cancelada por error",
    }
    response = sales_put(f"/{test_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["description"] == "Venta cancelada por error"


def test_update_sale_user_and_branch(
    auth_headers,
    test_sale,
    test_user_with_role_permissions_branch_auth,
    test_branch,
):
    payload = {
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "branch_id": test_branch.id,
    }
    response = sales_put(f"/{test_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == payload["user_id"]
    assert data["branch_id"] == payload["branch_id"]


def test_update_sale_not_found(auth_headers):
    payload = {"status": "cancelled"}
    response = sales_put("/9999", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale not found."


def test_update_sale_invalid_user(auth_headers, test_sale, test_branch):
    payload = {"user_id": 9999, "branch_id": test_branch.id}
    response = sales_put(f"/{test_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User ID does not exist."


def test_update_sale_invalid_branch(auth_headers, test_sale, test_user_with_role_permissions_branch_auth):
    payload = {"user_id": test_user_with_role_permissions_branch_auth.id, "branch_id": 9999}
    response = sales_put(f"/{test_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Branch ID does not exist."


def test_update_sale_invalid_status(auth_headers, test_sale):
    payload = {"status": "invalid_status"}
    response = sales_put(f"/{test_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["field"] == "status"


def test_update_completed_sale_rejected(auth_headers, completed_sale):
    # Una venta completada no se puede modificar
    payload = {"description": "Intento de modificación"}
    response = sales_put(f"/{completed_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Only draft sales can be modified."


def test_update_sale_refund_status_rejected(auth_headers, test_sale):
    # Los estados de refund solo los pone el sistema, no el usuario
    payload = {"status": "refunded"}
    response = sales_put(f"/{test_sale.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Refund statuses" in response.json()["detail"]


def test_update_sale_no_auth(test_sale):
    payload = {"status": "cancelled"}
    response = sales_put(f"/{test_sale.id}", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# DELETE
# ==================================================================
def test_delete_sale(auth_headers, test_sale):
    response = sales_delete(f"/{test_sale.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_sale_not_found(auth_headers):
    response = sales_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale not found."


def test_delete_sale_no_auth(test_sale):
    response = sales_delete(f"/{test_sale.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# POST /{sale_id}/complete
# ==================================================================
def test_complete_sale_success(
    auth_headers,
    test_sale,
    test_sale_detail,
    test_product_batch,
    db_session,
):
    initial_quantity = test_product_batch.quantity

    response = client.post(
        f"/api/v1/sales/{test_sale.id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "completed"

    # La venta se actualizó en DB
    db_session.refresh(test_sale)
    assert test_sale.status == "completed"

    # El stock se descontó
    db_session.refresh(test_product_batch)
    assert test_product_batch.quantity < initial_quantity

    # Se creó el SaleBatchUsage
    from pharmatrack.models.sale_batch_usage.orm import SaleBatchUsage
    usages = (
        db_session.query(SaleBatchUsage)
        .filter_by(sale_detail_id=test_sale_detail.id)
        .all()
    )
    assert len(usages) > 0


def test_complete_sale_not_found(auth_headers):
    response = client.post(
        "/api/v1/sales/9999/complete",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale not found"


def test_complete_sale_non_draft(auth_headers, completed_sale):
    # No se puede completar una venta que ya no está en draft
    response = client.post(
        f"/api/v1/sales/{completed_sale.id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Only draft sales can be completed"


def test_complete_sale_empty(auth_headers, empty_sale):
    # No se puede completar una venta sin detalles
    response = client.post(
        f"/api/v1/sales/{empty_sale.id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cannot complete an empty sale"


def test_complete_sale_insufficient_stock(
    auth_headers,
    test_sale,
    test_sale_detail,      # pide quantity=2
    product_batch_with_low_stock,  # stock=1
    db_session,
):
    response = client.post(
        f"/api/v1/sales/{test_sale.id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient stock" in response.json()["detail"]

    # La venta NO debe cambiar de estado
    db_session.refresh(test_sale)
    assert test_sale.status == "draft"


def test_complete_sale_no_auth(test_sale):
    response = client.post(f"/api/v1/sales/{test_sale.id}/complete")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED