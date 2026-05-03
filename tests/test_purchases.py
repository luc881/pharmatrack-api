from pharmatrack.api.routes.purchases import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
purchase_get, purchase_post, purchase_put, purchase_patch, purchase_delete = route_client_factory(client, "purchases")


# ------------------------------------------------------------------
# READ ALL
# ------------------------------------------------------------------
def test_read_all_purchases(auth_headers, test_purchase):
    response = purchase_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["total"] >= 1
    assert any(item["id"] == test_purchase.id for item in data["data"])


def test_read_all_purchases_no_auth():
    response = purchase_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# READ BY ID
# ------------------------------------------------------------------
def test_read_purchase_by_id(auth_headers, test_purchase):
    response = purchase_get(f"/{test_purchase.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_purchase.id
    assert data["supplier_id"] == test_purchase.supplier_id
    assert data["user_id"] == test_purchase.user_id
    assert data["total"] == test_purchase.total


def test_read_purchase_by_id_not_found(auth_headers):
    response = purchase_get("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase not found"


def test_read_purchase_by_id_no_auth(test_purchase):
    response = purchase_get(f"/{test_purchase.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
def test_create_purchase(auth_headers, test_supplier, test_user_with_role_permissions_branch_auth):
    payload = {
        "supplier_id": test_supplier.id,
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "total": 590.00,
        "description": "Compra de prueba",
    }
    response = purchase_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["supplier_id"] == payload["supplier_id"]
    assert data["user_id"] == payload["user_id"]
    assert data["total"] == payload["total"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "date_emision" in data


def test_create_purchase_invalid_supplier(auth_headers, test_user_with_role_permissions_branch_auth):
    payload = {
        "supplier_id": 9999,
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "total": 100.00,
    }
    response = purchase_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Supplier not found"


def test_create_purchase_invalid_user(auth_headers, test_supplier):
    payload = {
        "supplier_id": test_supplier.id,
        "user_id": 9999,
        "total": 100.00,
    }
    response = purchase_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_create_purchase_no_auth(test_supplier, test_user_with_role_permissions_branch_auth):
    payload = {
        "supplier_id": test_supplier.id,
        "user_id": test_user_with_role_permissions_branch_auth.id,
        "total": 100.00,
    }
    response = purchase_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
def test_update_purchase(auth_headers, test_purchase):
    payload = {
        "total": 2000.00,
        "description": "Descripción actualizada",
    }
    response = purchase_put(f"/{test_purchase.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_purchase.id
    assert data["total"] == payload["total"]
    assert data["description"] == payload["description"]


def test_update_purchase_not_found(auth_headers):
    payload = {"total": 999.00}
    response = purchase_put("/9999", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase not found"


def test_update_purchase_invalid_supplier(auth_headers, test_purchase):
    payload = {"supplier_id": 9999}
    response = purchase_put(f"/{test_purchase.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Supplier not found"


def test_update_purchase_invalid_user(auth_headers, test_purchase):
    payload = {"user_id": 9999}
    response = purchase_put(f"/{test_purchase.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_update_purchase_no_auth(test_purchase):
    payload = {"total": 999.00}
    response = purchase_put(f"/{test_purchase.id}", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
def test_delete_purchase(auth_headers, test_purchase):
    response = purchase_delete(f"/{test_purchase.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_purchase_not_found(auth_headers):
    response = purchase_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase not found"


def test_delete_purchase_no_auth(test_purchase):
    response = purchase_delete(f"/{test_purchase.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED