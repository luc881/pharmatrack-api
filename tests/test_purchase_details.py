from pharmatrack.api.routes.purchase_details import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
detail_get, detail_post, detail_put, detail_patch, detail_delete = route_client_factory(client, "purchase-details")


# ------------------------------------------------------------------
# READ ALL
# ------------------------------------------------------------------
def test_read_all_purchase_details(auth_headers, test_purchase_detail):
    response = detail_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_purchase_detail.id for item in data)


def test_read_all_purchase_details_no_auth():
    response = detail_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# READ BY ID
# ------------------------------------------------------------------
def test_read_purchase_detail_by_id(auth_headers, test_purchase_detail):
    response = detail_get(f"/{test_purchase_detail.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_purchase_detail.id
    assert data["purchase_id"] == test_purchase_detail.purchase_id
    assert data["product_id"] == test_purchase_detail.product_id
    assert data["quantity"] == test_purchase_detail.quantity
    assert data["unit_price"] == test_purchase_detail.unit_price
    assert data["lot_code"] == test_purchase_detail.lot_code


def test_read_purchase_detail_by_id_not_found(auth_headers):
    response = detail_get("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase detail not found"


def test_read_purchase_detail_by_id_no_auth(test_purchase_detail):
    response = detail_get(f"/{test_purchase_detail.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
def test_create_purchase_detail(auth_headers, test_purchase, test_product):
    payload = {
        "purchase_id": test_purchase.id,
        "product_id": test_product.id,
        "quantity": 20.0,
        "unit_price": 50.0,
        "expiration_date": "2027-06-30",
        "lot_code": "LOT-2025-003",
    }
    response = detail_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["purchase_id"] == payload["purchase_id"]
    assert data["product_id"] == payload["product_id"]
    assert data["quantity"] == payload["quantity"]
    assert data["unit_price"] == payload["unit_price"]
    assert data["expiration_date"] == payload["expiration_date"]
    assert data["lot_code"] == payload["lot_code"]
    assert "id" in data
    assert "created_at" in data


def test_create_purchase_detail_invalid_purchase(auth_headers, test_product):
    payload = {
        "purchase_id": 9999,
        "product_id": test_product.id,
        "quantity": 10.0,
        "unit_price": 50.0,
    }
    response = detail_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase not found"


def test_create_purchase_detail_invalid_product(auth_headers, test_purchase):
    payload = {
        "purchase_id": test_purchase.id,
        "product_id": 9999,
        "quantity": 10.0,
        "unit_price": 50.0,
    }
    response = detail_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"


def test_create_purchase_detail_no_auth(test_purchase, test_product):
    payload = {
        "purchase_id": test_purchase.id,
        "product_id": test_product.id,
        "quantity": 10.0,
        "unit_price": 50.0,
    }
    response = detail_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
def test_update_purchase_detail(auth_headers, test_purchase_detail):
    payload = {
        "quantity": 25.0,
        "unit_price": 45.0,
        "expiration_date": "2028-01-15",
        "lot_code": "LOT-2025-999",
    }
    response = detail_put(f"/{test_purchase_detail.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_purchase_detail.id
    assert data["quantity"] == payload["quantity"]
    assert data["unit_price"] == payload["unit_price"]
    assert data["expiration_date"] == payload["expiration_date"]
    assert data["lot_code"] == payload["lot_code"]


def test_update_purchase_detail_not_found(auth_headers):
    payload = {"quantity": 5.0}
    response = detail_put("/9999", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase detail not found"


def test_update_purchase_detail_no_auth(test_purchase_detail):
    payload = {"quantity": 5.0}
    response = detail_put(f"/{test_purchase_detail.id}", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
def test_delete_purchase_detail(auth_headers, test_purchase_detail):
    response = detail_delete(f"/{test_purchase_detail.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_purchase_detail_not_found(auth_headers):
    response = detail_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Purchase detail not found"


def test_delete_purchase_detail_no_auth(test_purchase_detail):
    response = detail_delete(f"/{test_purchase_detail.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED