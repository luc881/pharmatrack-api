from pharmatrack.api.routes.sale_payments import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
sp_get, sp_post, sp_put, sp_patch, sp_delete = route_client_factory(client, "salepayments")


# ==================================================================
# READ ALL  (lista plana, no paginada)
# ==================================================================
def test_read_all_sale_payments(auth_headers, test_sale_payment):
    response = sp_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_sale_payment.id for item in data)


def test_read_all_sale_payments_no_auth():
    response = sp_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# CREATE
# ==================================================================
def test_create_sale_payment(auth_headers, test_sale):
    payload = {
        "sale_id": test_sale.id,
        "method_payment": "card",
        "transaction_number": "TX123456789",
        "bank": "BBVA",
        "amount": 100.00,
    }
    response = sp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["sale_id"] == payload["sale_id"]
    assert data["method_payment"] == payload["method_payment"]
    assert data["transaction_number"] == payload["transaction_number"]
    assert data["bank"] == payload["bank"]
    assert float(data["amount"]) == payload["amount"]
    assert "id" in data
    assert "created_at" in data


def test_create_sale_payment_cash(auth_headers, test_sale):
    payload = {
        "sale_id": test_sale.id,
        "method_payment": "cash",
        "amount": 50.00,
    }
    response = sp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["method_payment"] == "cash"
    assert data["transaction_number"] is None
    assert data["bank"] is None


def test_create_sale_payment_invalid_sale(auth_headers):
    payload = {
        "sale_id": 9999,
        "method_payment": "cash",
        "amount": 100.00,
    }
    response = sp_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated sale not found"


def test_create_sale_payment_no_auth(test_sale):
    payload = {
        "sale_id": test_sale.id,
        "method_payment": "cash",
        "amount": 50.00,
    }
    response = sp_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# UPDATE
# ==================================================================
def test_update_sale_payment(auth_headers, test_sale_payment):
    payload = {
        "method_payment": "transfer",
        "bank": "Santander",
        "amount": 150.00,
    }
    response = sp_put(f"/{test_sale_payment.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["method_payment"] == payload["method_payment"]
    assert data["bank"] == payload["bank"]
    assert float(data["amount"]) == payload["amount"]
    # Campos no enviados no cambian
    assert data["id"] == test_sale_payment.id
    assert data["sale_id"] == test_sale_payment.sale_id


def test_update_sale_payment_not_found(auth_headers):
    response = sp_put("/9999", json={"amount": 50.00}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale payment not found"


def test_update_sale_payment_invalid_sale(auth_headers, test_sale_payment):
    payload = {"sale_id": 9999, "amount": 150.00}
    response = sp_put(f"/{test_sale_payment.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated sale not found"


def test_update_sale_payment_no_auth(test_sale_payment):
    response = sp_put(f"/{test_sale_payment.id}", json={"amount": 50.00})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# DELETE  (soft delete — 204, el registro queda con deleted_at)
# ==================================================================
def test_delete_sale_payment(auth_headers, test_sale_payment):
    response = sp_delete(f"/{test_sale_payment.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_sale_payment_not_found(auth_headers):
    response = sp_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale payment not found"


def test_delete_sale_payment_no_auth(test_sale_payment):
    response = sp_delete(f"/{test_sale_payment.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED