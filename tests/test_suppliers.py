from pharmatrack.api.routes.suppliers import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
suppliers_get, suppliers_post, suppliers_put, suppliers_patch, suppliers_delete = route_client_factory(client, "suppliers")


# ------------------------------------------------------------------
# READ ALL
# ------------------------------------------------------------------
def test_read_all_suppliers(auth_headers, test_supplier):
    response = suppliers_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["total"] >= 1
    assert any(item["id"] == test_supplier.id for item in data["data"])


def test_read_all_suppliers_no_auth():
    response = suppliers_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# READ BY ID
# ------------------------------------------------------------------
def test_read_supplier_by_id(auth_headers, test_supplier):
    response = suppliers_get(f"/{test_supplier.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_supplier.id
    assert data["name"] == test_supplier.name
    assert data["email"] == test_supplier.email


def test_read_supplier_by_id_not_found(auth_headers):
    response = suppliers_get("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Supplier not found"


def test_read_supplier_by_id_no_auth(test_supplier):
    response = suppliers_get(f"/{test_supplier.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
def test_create_supplier(auth_headers):
    payload = {
        "name": "Distribuidora Nueva S.A.",
        "logo": "https://example.com/logo_nueva.png",
        "email": "nueva@distribuidora.com",
        "phone": "+525551112222",
        "address": "Calle Nueva 456, CDMX",
        "rfc": "NUE123456789",
        "is_active": True,
    }
    response = suppliers_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["logo"] == payload["logo"]
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["address"] == payload["address"]
    assert data["rfc"] == payload["rfc"]
    assert data["is_active"] == payload["is_active"]


def test_create_supplier_duplicate_email(auth_headers, test_supplier):
    payload = {
        "name": "Otra Distribuidora S.A.",
        "email": test_supplier.email,  # duplicado
        "rfc": "OTRO999999999",
        "is_active": True,
    }
    response = suppliers_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already in use"


def test_create_supplier_duplicate_rfc(auth_headers, test_supplier):
    payload = {
        "name": "Otra Distribuidora S.A.",
        "email": "otro@email.com",
        "rfc": test_supplier.rfc,  # duplicado
        "is_active": True,
    }
    response = suppliers_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "RFC already in use"


def test_create_supplier_no_auth():
    payload = {
        "name": "Sin Auth S.A.",
        "is_active": True,
    }
    response = suppliers_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
def test_update_supplier(auth_headers, test_supplier):
    payload = {
        "name": "Distribuidora Abc S.A. De C.V.",
        "phone": "+525559876543",
        "is_active": False,
    }
    response = suppliers_put(f"/{test_supplier.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_supplier.id
    assert data["name"] == payload["name"]
    assert data["phone"] == payload["phone"]
    assert data["is_active"] == payload["is_active"]


def test_update_supplier_not_found(auth_headers):
    payload = {"name": "No existe"}
    response = suppliers_put("/9999", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Supplier not found"


def test_update_supplier_duplicate_email(auth_headers, test_supplier, another_supplier):
    payload = {"email": another_supplier.email}  # duplicado
    response = suppliers_put(f"/{test_supplier.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already in use"


def test_update_supplier_duplicate_rfc(auth_headers, test_supplier, another_supplier):
    payload = {"rfc": another_supplier.rfc}  # duplicado
    response = suppliers_put(f"/{test_supplier.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "RFC already in use"


def test_update_supplier_no_auth(test_supplier):
    payload = {"name": "Sin Auth"}
    response = suppliers_put(f"/{test_supplier.id}", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
def test_delete_supplier(auth_headers, test_supplier):
    response = suppliers_delete(f"/{test_supplier.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_supplier_not_found(auth_headers):
    response = suppliers_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Supplier not found"


def test_delete_supplier_no_auth(test_supplier):
    response = suppliers_delete(f"/{test_supplier.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED