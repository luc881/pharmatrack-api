from pharmatrack.api.routes.ingredients import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
ingredient_get, ingredient_post, ingredient_put, ingredient_patch, ingredient_delete = route_client_factory(client, prefix="ingredients")


# =========================================================
# 🔹 GET /
# =========================================================

def test_read_all_empty(auth_headers):
    response = ingredient_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert isinstance(data["data"], list)


def test_read_all_with_data(auth_headers, test_ingredient):
    response = ingredient_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    ids = [i["id"] for i in data["data"]]
    assert test_ingredient.id in ids


def test_read_all_unauthenticated():
    response = ingredient_get()
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_ingredient(auth_headers):
    new_ingredient = {
        "name": "ibuprofeno",
        "description": "Analgésico y antiinflamatorio"
    }
    response = ingredient_post(json=new_ingredient, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "ibuprofeno"
    assert data["description"] == "Analgésico y antiinflamatorio"


def test_create_ingredient_strip_and_lowercase(auth_headers):
    new_ingredient = {
        "name": "  Ibuprofeno  ",
        "description": "Analgésico y antiinflamatorio"
    }
    response = ingredient_post(json=new_ingredient, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "ibuprofeno"


def test_create_ingredient_invalid_name(auth_headers):
    response = ingredient_post(json={"name": "Ibuprofeno!!!", "description": "test"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_ingredient_duplicate(auth_headers, test_ingredient):
    response = ingredient_post(json={"name": test_ingredient.name, "description": "dup"}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Ingredient with this name already exists."


def test_create_ingredient_missing_name(auth_headers):
    response = ingredient_post(json={"description": "no name"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_ingredient_unauthenticated():
    response = ingredient_post(json={"name": "ibuprofeno", "description": "test"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 PUT /{ingredient_id}
# =========================================================

def test_update_ingredient_description(auth_headers, test_ingredient):
    response = ingredient_put(str(test_ingredient.id), json={"description": "Updated description"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["description"] == "Updated description"


def test_update_ingredient_name(auth_headers, test_ingredient):
    response = ingredient_put(str(test_ingredient.id), json={"name": "aspirina"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "aspirina"


def test_update_ingredient_strip_and_lowercase(auth_headers, test_ingredient):
    response = ingredient_put(str(test_ingredient.id), json={"name": "  Ibuprofeno  "}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "ibuprofeno"


def test_update_ingredient_name_to_existing(auth_headers, test_ingredient, another_test_ingredient):
    response = ingredient_put(
        str(test_ingredient.id),
        json={"name": another_test_ingredient.name},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Ingredient with this name already exists."


def test_update_ingredient_invalid_name(auth_headers, test_ingredient):
    response = ingredient_put(str(test_ingredient.id), json={"name": "Ibuprofeno!!!"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_ingredient_not_found(auth_headers):
    response = ingredient_put("9999", json={"description": "Updated"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Ingredient not found."


def test_update_ingredient_unauthenticated(test_ingredient):
    response = ingredient_put(str(test_ingredient.id), json={"description": "Updated"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# 🔹 DELETE /{ingredient_id}
# =========================================================

def test_delete_ingredient(auth_headers, test_ingredient):
    response = ingredient_delete(str(test_ingredient.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_ingredient_verify_gone(auth_headers, test_ingredient):
    ingredient_delete(str(test_ingredient.id), headers=auth_headers)
    # Verificar que ya no aparece en el listado
    response = ingredient_get(headers=auth_headers)
    ids = [i["id"] for i in response.json()["data"]]
    assert test_ingredient.id not in ids


def test_delete_ingredient_not_found(auth_headers):
    response = ingredient_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Ingredient not found."


def test_delete_ingredient_unauthenticated(test_ingredient):
    response = ingredient_delete(str(test_ingredient.id))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED