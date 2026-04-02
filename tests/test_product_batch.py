import pytest
from datetime import date

from pharmatrack.api.routes.product_batch import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
batch_get, batch_post, batch_put, batch_patch, batch_delete = route_client_factory(client, "productsbatches")


# =========================================================
# 🔹 Fixtures locales
# =========================================================

@pytest.fixture
def test_product_batch(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="LOT123456",
        expiration_date=date(2026, 12, 31),
        quantity=100,
        purchase_price=5.50,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def another_product_batch(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="LOT654321",
        expiration_date=date(2026, 6, 30),
        quantity=50,
        purchase_price=6.00,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


# Útil para tests de sale_batch_usage — lo definimos aquí para reutilizar
@pytest.fixture
def product_batch_with_stock(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="L001",
        expiration_date=date(2026, 1, 1),
        quantity=100,
        purchase_price=10.0,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def product_batch_with_low_stock(db_session, test_product):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(
        product_id=test_product.id,
        lot_code="L002",
        expiration_date=date(2026, 1, 1),
        quantity=1,
        purchase_price=10.0,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


# =========================================================
# 🔹 GET /
# =========================================================

def test_read_all_product_batches(auth_headers, test_product_batch):
    response = batch_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["total"] >= 1
    ids = [b["id"] for b in data["data"]]
    assert test_product_batch.id in ids


def test_read_all_product_batches_no_auth():
    response = batch_get()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 GET /details
# =========================================================

def test_read_all_product_batches_with_details(auth_headers, test_product_batch):
    response = batch_get("details", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["total"] >= 1
    item = next((b for b in data["data"] if b["id"] == test_product_batch.id), None)
    assert item is not None
    assert "product" in item
    # Comparamos product_id desde el fixture, no desde la relación ORM (evita DetachedInstanceError)
    assert item["product"]["id"] == test_product_batch.product_id


def test_read_all_product_batches_with_details_no_auth():
    response = batch_get("details")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 GET /{id}
# =========================================================

def test_read_product_batch_by_id(auth_headers, test_product_batch):
    response = batch_get(str(test_product_batch.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_product_batch.id
    assert data["lot_code"] == test_product_batch.lot_code
    assert data["product_id"] == test_product_batch.product_id
    assert "product" in data
    assert data["product"]["id"] == test_product_batch.product_id


def test_read_product_batch_by_id_not_found(auth_headers):
    response = batch_get("999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product batch not found."


def test_read_product_batch_by_id_no_auth(test_product_batch):
    response = batch_get(str(test_product_batch.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_product_batch(auth_headers, test_product):
    payload = {
        "product_id": test_product.id,
        "lot_code": "A2025-01",
        "expiration_date": "2026-12-15",
        "quantity": 100,
        "purchase_price": 12.50,
    }
    response = batch_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["lot_code"] == "A2025-01"
    assert data["product_id"] == test_product.id
    assert data["quantity"] == 100


def test_create_product_batch_invalid_product(auth_headers):
    payload = {
        "product_id": 999999,
        "lot_code": "B2025-02",
        "expiration_date": "2026-11-30",
        "quantity": 50,
        "purchase_price": 10.00,
    }
    response = batch_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Product with the given ID does not exist."


def test_create_product_batch_duplicate_lot_code(auth_headers, test_product, test_product_batch):
    payload = {
        "product_id": test_product.id,
        "lot_code": test_product_batch.lot_code,
        "expiration_date": "2026-12-31",
        "quantity": 200,
        "purchase_price": 15.00,
    }
    response = batch_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "A batch with this lot_code already exists for this product."


def test_create_product_batch_no_auth(test_product):
    payload = {
        "product_id": test_product.id,
        "lot_code": "UNAUTH01",
        "expiration_date": "2026-12-15",
        "quantity": 100,
        "purchase_price": 12.50,
    }
    response = batch_post(json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 PUT /{id}
# =========================================================

def test_update_product_batch(auth_headers, test_product_batch):
    payload = {
        "quantity": 80,
        "expiration_date": "2026-11-30",
    }
    response = batch_put(str(test_product_batch.id), json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["quantity"] == 80
    assert data["expiration_date"] == "2026-11-30"


def test_update_product_batch_not_found(auth_headers):
    response = batch_put("999999", json={"quantity": 80}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product batch not found."


def test_update_product_batch_no_auth(test_product_batch):
    response = batch_put(str(test_product_batch.id), json={"quantity": 80})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_product_batch_duplicate_lot_code(auth_headers, test_product_batch, another_product_batch):
    # Intentar asignarle a another_product_batch el lot_code de test_product_batch → duplicado
    payload = {"lot_code": test_product_batch.lot_code}
    response = batch_put(str(another_product_batch.id), json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "A batch with this lot_code already exists for this product."


# =========================================================
# 🔹 DELETE /{id}
# =========================================================

def test_delete_product_batch(auth_headers, test_product_batch):
    response = batch_delete(str(test_product_batch.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que ya no existe
    response = batch_get(str(test_product_batch.id), headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_product_batch_not_found(auth_headers):
    response = batch_delete("999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product batch not found."


def test_delete_product_batch_no_auth(test_product_batch):
    response = batch_delete(str(test_product_batch.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED