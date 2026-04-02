import pytest
from pharmatrack.api.routes.product_master import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
prodMaster_get, prodMaster_post, prodMaster_put, prodMaster_patch, prodMaster_delete = route_client_factory(client, "productsmaster")


# =========================================================
# Fixtures — sin product_category_id (no existe en el ORM)
# =========================================================

@pytest.fixture
def test_product_master(db_session):
    from pharmatrack.models.product_master.orm import ProductMaster
    from pharmatrack.utils.slugify import slugify
    name = "Paracetamol"
    master = ProductMaster(
        name=name,
        slug=slugify(name),
        description="Medicamento para aliviar el dolor y reducir la fiebre",
    )
    db_session.add(master)
    db_session.commit()
    db_session.refresh(master)
    return master


@pytest.fixture
def another_product_master(db_session):
    from pharmatrack.models.product_master.orm import ProductMaster
    from pharmatrack.utils.slugify import slugify
    name = "Ibuprofeno"
    master = ProductMaster(
        name=name,
        slug=slugify(name),
        description="Medicamento antiinflamatorio y analgésico",
    )
    db_session.add(master)
    db_session.commit()
    db_session.refresh(master)
    return master


# =========================================================
# 🔹 GET /
# =========================================================

def test_read_all_empty(auth_headers):
    response = prodMaster_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_read_all_with_data(auth_headers, test_product_master):
    response = prodMaster_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    ids = [m["id"] for m in data["data"]]
    assert test_product_master.id in ids


def test_read_all_no_auth():
    response = prodMaster_get()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 GET /{master_id}
# =========================================================

def test_read_master_by_id(auth_headers, test_product_master):
    response = prodMaster_get(str(test_product_master.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_product_master.id
    assert data["name"] == test_product_master.name


def test_read_master_by_id_not_found(auth_headers):
    response = prodMaster_get("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_read_master_by_id_no_auth(test_product_master):
    response = prodMaster_get(str(test_product_master.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_master(auth_headers):
    payload = {
        "name": "Aspirina",
        "description": "Medicamento para el dolor de cabeza",
    }
    response = prodMaster_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]


def test_create_master_duplicate(auth_headers, test_product_master):
    payload = {
        "name": test_product_master.name,
        "description": "Otro medicamento",
    }
    response = prodMaster_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_create_master_missing_name(auth_headers):
    response = prodMaster_post(json={"description": "Sin nombre"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_master_no_auth():
    response = prodMaster_post(json={"name": "Sin auth", "description": "Desc"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 PUT /{master_id}
# =========================================================

def test_update_master(auth_headers, test_product_master):
    payload = {
        "name": "Nuevo nombre",
        "description": "Descripción actualizada",
    }
    response = prodMaster_put(str(test_product_master.id), json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]


def test_update_master_duplicate_name(auth_headers, test_product_master, another_product_master):
    payload = {"name": another_product_master.name}
    response = prodMaster_put(str(test_product_master.id), json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_update_master_not_found(auth_headers):
    response = prodMaster_put("9999", json={"name": "Ghost"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_update_master_no_auth(test_product_master):
    response = prodMaster_put(str(test_product_master.id), json={"name": "Sin auth"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 PUT parcial (solo un campo a la vez)
# =========================================================

def test_partial_update_only_name(auth_headers, test_product_master):
    response = prodMaster_put(
        str(test_product_master.id),
        json={"name": "Solo nombre"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Solo nombre"
    assert data["description"] == test_product_master.description


def test_partial_update_only_description(auth_headers, test_product_master):
    response = prodMaster_put(
        str(test_product_master.id),
        json={"description": "Solo descripción"},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Solo descripción"
    assert data["name"] == test_product_master.name


def test_partial_update_empty_payload(auth_headers, test_product_master):
    """Payload vacío no debe cambiar nada."""
    response = prodMaster_put(str(test_product_master.id), json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == test_product_master.name
    assert data["description"] == test_product_master.description


def test_partial_update_duplicate_name(auth_headers, test_product_master, another_product_master):
    response = prodMaster_put(
        str(test_product_master.id),
        json={"name": another_product_master.name},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_partial_update_no_auth(test_product_master):
    response = prodMaster_put(str(test_product_master.id), json={"name": "Sin auth"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 DELETE /{master_id}
# =========================================================

def test_delete_master(auth_headers, test_product_master):
    response = prodMaster_delete(str(test_product_master.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_master_verify_gone(auth_headers, test_product_master):
    prodMaster_delete(str(test_product_master.id), headers=auth_headers)
    response = prodMaster_get(str(test_product_master.id), headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_master_not_found(auth_headers):
    response = prodMaster_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"]


def test_delete_master_no_auth(test_product_master):
    response = prodMaster_delete(str(test_product_master.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED