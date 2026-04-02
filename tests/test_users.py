from pharmatrack.api.routes.users import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db

# ✅ El factory ya agrega /api/v1 automáticamente
users_get, users_post, users_put, users_patch, users_delete = route_client_factory(client, "users")


# =========================================================
# 🔹 GET endpoints
# =========================================================

def test_read_all_users(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # ✅ Paginación: los items están en data["data"]
    assert "data" in data
    assert "total" in data
    assert isinstance(data["data"], list)
    assert any(user["id"] == test_user_with_role_permissions_branch_auth.id for user in data["data"])


def test_read_user_by_id(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get(f"/{test_user_with_role_permissions_branch_auth.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user_with_role_permissions_branch_auth.id
    assert data["email"] == test_user_with_role_permissions_branch_auth.email
    assert data["branch_id"] == test_user_with_role_permissions_branch_auth.branch_id
    assert data["role_id"] == test_user_with_role_permissions_branch_auth.role_id


def test_read_user_by_id_not_found(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_read_user_details(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get(f"/{test_user_with_role_permissions_branch_auth.id}/details", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user_with_role_permissions_branch_auth.id
    assert data["branch"]["id"] == test_user_with_role_permissions_branch_auth.branch_id
    assert data["role"]["id"] == test_user_with_role_permissions_branch_auth.role_id


def test_read_user_details_not_found(auth_headers):
    response = users_get("/9999/details", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


# =========================================================
# 🔹 GET /search
# =========================================================

def test_search_filter_by_name(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"name": "Test"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any("test" in user["name"].lower() for user in data["data"])


def test_search_filter_by_surname(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"surname": "User"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["surname"] == "user surname"


def test_search_filter_by_email_case_insensitive(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"email": "test@example.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["email"] == "test@example.com"


def test_search_filter_by_branch_and_role(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"branch_id": 1, "role_id": 1}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(u["name"] == "testuser" for u in data["data"])


def test_search_filter_by_phone_partial(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"phone": "2222"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any("2222" in user["phone"] for user in data["data"])


def test_search_filter_by_gender(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"gender": "M"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(user["gender"] == "M" for user in data["data"])


def test_search_filter_by_type_document_partial(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"type_document": "IN"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any("IN" in user["type_document"] for user in data["data"])


def test_search_filter_by_n_document_partial(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", params={"n_document": "ABC"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any("ABC" in user["n_document"] for user in data["data"])


def test_search_no_filters(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_get("/search", headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Debe especificar al menos un filtro para la búsqueda"


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_user(auth_headers):
    new_user = {
        "name": "Juan",
        "surname": "Pérez",
        "email": "juan.perez@example.com",
        "password": "secureMpassword123",
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2221548560",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M"
    }
    response = users_post(json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Juan"
    assert data["email"] == "juan.perez@example.com"
    assert data["avatar"] == "http://example.com/avatar.jpg"


def test_create_user_already_created(test_user_with_role_permissions_branch_auth, auth_headers):
    new_user = {
        "name": "Test User",
        "surname": "User Surname",
        "email": "test@example.com",
        "password": "secureMpassword123",
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2222222222",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M"
    }
    response = users_post(json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_create_user_with_role(test_user_with_role_permissions_branch_auth, auth_headers):
    new_user = {
        "name": "Test User",
        "surname": "User Surname",
        "email": "test2@example.com",
        "password": "secureMpassword123",
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2222222222",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M",
        "role_id": test_user_with_role_permissions_branch_auth.role_id
    }
    response = users_post(json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["role_id"] == test_user_with_role_permissions_branch_auth.role_id


def test_create_user_with_role_not_found(auth_headers):
    new_user = {
        "name": "Test User",
        "surname": "User Surname",
        "email": "test2@example.com",
        "password": "secureMpassword123",
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2222222222",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M",
        "role_id": 9999
    }
    response = users_post(json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_user_with_branch_not_found(auth_headers):
    new_user = {
        "name": "Test User",
        "surname": "User Surname",
        "email": "test2@example.com",
        "password": "secureMpassword123",
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2222222222",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M",
        "branch_id": 99999
    }
    response = users_post(json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Branch not found"


def test_create_user_with_branch(auth_headers):
    new_user = {
        "name": "Test User",
        "surname": "User Surname",
        "email": "test2@example.com",
        "password": "secureMpassword123",
        "avatar": "http://example.com/avatar.jpg",
        "phone": "2222222222",
        "type_document": "INE",
        "n_document": "ABC123456",
        "gender": "M",
        "branch_id": 1
    }
    response = users_post(json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test User"


# =========================================================
# 🔹 PUT /{user_id}
# =========================================================

def test_update_user(test_user_with_role_permissions_branch_auth, auth_headers):
    update_user = {
        "name": "TestUser",
        "surname": "User Surname",
        "email": "test2@example.com",
        "avatar": "http://example.com/avatar2.jpg",
        "phone": "2225156581",
        "type_document": "LICENSE",
        "n_document": "ABC1234562",
        "gender": "F"
    }
    response = users_put(f"/{test_user_with_role_permissions_branch_auth.id}", json=update_user, headers=auth_headers)
    if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        print("\nDEBUG Response JSON:", response.json())
    assert response.status_code == status.HTTP_200_OK


def test_update_user_not_found(auth_headers):
    update_user = {
        "name": "TestUser",
        "surname": "User Surname",
        "email": "test2@example.com",
        "avatar": "http://example.com/avatar2.jpg",
        "phone": "2225156581",
        "type_document": "LICENSE",
        "n_document": "ABC1234562",
        "gender": "F"
    }
    response = users_put("/9999", json=update_user, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_user_with_branch(test_user_with_role_permissions_branch_auth, auth_headers):
    update_user = {
        "name": "TestUser",
        "surname": "User Surname",
        "email": "test2@example.com",
        "avatar": "http://example.com/avatar2.jpg",
        "phone": "2225156581",
        "type_document": "LICENSE",
        "n_document": "ABC1234562",
        "gender": "F",
        "branch_id": 1
    }
    response = users_put(f"/{test_user_with_role_permissions_branch_auth.id}", json=update_user, headers=auth_headers)
    if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        print("\nDEBUG Response JSON:", response.json())
    assert response.status_code == status.HTTP_200_OK


def test_update_user_with_branch_not_found(test_user_with_role_permissions_branch_auth, auth_headers):
    update_user = {
        "name": "TestUser",
        "surname": "User Surname",
        "email": "test2@example.com",
        "avatar": "http://example.com/avatar2.jpg",
        "phone": "2225156581",
        "type_document": "LICENSE",
        "n_document": "ABC1234562",
        "gender": "F",
        "branch_id": 9999
    }
    response = users_put(f"/{test_user_with_role_permissions_branch_auth.id}", json=update_user, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_user_with_role(test_user_with_role_permissions_branch_auth, auth_headers):
    new_user = {
        "name": "TestUser",
        "surname": "User Surname",
        "email": "test2@example.com",
        "avatar": "http://example.com/avatar2.jpg",
        "phone": "2225156581",
        "type_document": "LICENSE",
        "n_document": "ABC1234562",
        "gender": "F",
        "role_id": test_user_with_role_permissions_branch_auth.role_id
    }
    response = users_put(f"/{test_user_with_role_permissions_branch_auth.id}", json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["role_id"] == test_user_with_role_permissions_branch_auth.role_id


def test_update_user_with_role_not_found(test_user_with_role_permissions_branch_auth, auth_headers):
    new_user = {
        "name": "TestUser",
        "surname": "User Surname",
        "email": "test2@example.com",
        "avatar": "http://example.com/avatar2.jpg",
        "phone": "2225156581",
        "type_document": "LICENSE",
        "n_document": "ABC1234562",
        "gender": "F",
        "role_id": 9999
    }
    response = users_put(f"/{test_user_with_role_permissions_branch_auth.id}", json=new_user, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# =========================================================
# 🔹 DELETE /{user_id}
# =========================================================

def test_delete_user(test_user_with_role_permissions_branch_auth, auth_headers):
    response = users_delete(f"/{test_user_with_role_permissions_branch_auth.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_user_not_found(auth_headers):
    response = users_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# =========================================================
# 🔹 PUT /{user_id}/change-password
# =========================================================

def test_change_password_success(test_user_with_role_permissions_branch_auth, auth_headers):
    payload = {
        "old_password": "secureMpassword123",
        "new_password": "NewPassword123"
    }
    response = users_put(
        f"/{test_user_with_role_permissions_branch_auth.id}/change-password",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Contraseña actualizada correctamente"


def test_change_password_user_not_found(auth_headers):
    payload = {
        "old_password": "anything123",
        "new_password": "NewPassword123"
    }
    response = users_put("/99999/change-password", json=payload, headers=auth_headers)
    # Identity check (token owner != user_id) fires before the DB lookup
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_change_password_incorrect_old(test_user_with_role_permissions_branch_auth, auth_headers):
    payload = {
        "old_password": "incorrect_password",
        "new_password": "NewPassword123"
    }
    response = users_put(
        f"/{test_user_with_role_permissions_branch_auth.id}/change-password",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "La contraseña anterior es incorrecta"


def test_change_password_weak_new_password(test_user_with_role_permissions_branch_auth, auth_headers):
    payload = {
        "old_password": "secureMpassword123",
        "new_password": "abc"
    }
    response = users_put(
        f"/{test_user_with_role_permissions_branch_auth.id}/change-password",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert any(
        "no cumple los requisitos" in err.get("msg", "").lower() or
        "debe tener al menos 8 caracteres" in err.get("msg", "").lower()
        for err in errors
    )


def test_change_password_missing_fields(test_user_with_role_permissions_branch_auth, auth_headers):
    payload = {
        "old_password": "secureMpassword123"
        # falta new_password
    }
    response = users_put(
        f"/{test_user_with_role_permissions_branch_auth.id}/change-password",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_change_password_same_as_old(test_user_with_role_permissions_branch_auth, auth_headers):
    payload = {
        "old_password": "secureMpassword123",
        "new_password": "secureMpassword123"
    }
    response = users_put(
        f"/{test_user_with_role_permissions_branch_auth.id}/change-password",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "nueva contraseña no puede ser igual" in response.json()["detail"].lower()


def test_change_password_not_authorized(test_user_with_role_permissions_branch_auth):
    payload = {
        "old_password": "secureMpassword123",
        "new_password": "NewPassword123"
    }
    response = users_put(
        f"/{test_user_with_role_permissions_branch_auth.id}/change-password",
        json=payload
        # sin headers
    )
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)