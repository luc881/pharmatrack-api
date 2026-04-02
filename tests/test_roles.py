from pharmatrack.api.routes.roles import get_db as original_get_db
from fastapi import status
from .utils import override_get_db, app, client, route_client_factory

app.dependency_overrides[original_get_db] = override_get_db
roles_get, roles_post, roles_put, roles_patch, roles_delete = route_client_factory(client, "roles")

# Nombres que no colisionan con el fixture de auth
ROLE_A = "supervisor"
ROLE_B = "auditor"
PERM_EXTRA = "reports.read"


# =========================================================
# 🔹 GET /
# =========================================================

def test_read_all_with_data(auth_headers):
    """auth_headers ya crea el rol 'manager'."""
    response = roles_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1
    names = [r["name"] for r in data["data"]]
    assert "manager" in names


# =========================================================
# 🔹 GET /permissions
# =========================================================

def test_read_all_with_permissions(auth_headers, test_role_with_permissions_and_authentication):
    response = roles_get("permissions", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["total"] >= 1
    role_names = [r["name"] for r in data["data"]]
    assert "manager" in role_names
    manager = next(r for r in data["data"] if r["name"] == "manager")
    perm_names = [p["name"] for p in manager["permissions"]]
    assert "users.read" in perm_names


# =========================================================
# 🔹 GET /{role_id}
# =========================================================

def test_read_by_id_with_permissions(auth_headers, test_role_with_permissions_and_authentication):
    role = test_role_with_permissions_and_authentication
    response = roles_get(str(role.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "manager"
    perm_names = [p["name"] for p in data["permissions"]]
    assert "users.read" in perm_names


def test_read_by_id_not_found(auth_headers):
    response = roles_get("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Role not found"}


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_role_without_permissions(auth_headers):
    response = roles_post(json={"name": ROLE_A}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == ROLE_A
    assert data["permissions"] == []


def test_create_role_with_permission_ids(auth_headers, make_permission):
    perm = make_permission(PERM_EXTRA)
    response = roles_post(json={"name": ROLE_A, "permission_ids": [perm.id]}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == ROLE_A
    assert any(p["name"] == PERM_EXTRA for p in data["permissions"])


def test_create_role_duplicate(auth_headers):
    """'manager' ya existe por el fixture auth_headers."""
    response = roles_post(json={"name": "manager"}, headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Role name already exists"}


def test_create_role_invalid_permission_id(auth_headers, make_permission):
    """Mezcla de IDs válidos e inválidos."""
    perm1 = make_permission("valid.one")
    perm2 = make_permission("valid.two")
    response = roles_post(
        json={"name": ROLE_A, "permission_ids": [perm1.id, perm2.id, 9999]},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Permissions not found: [9999]"}


def test_create_role_all_invalid_permission_ids(auth_headers):
    response = roles_post(
        json={"name": ROLE_A, "permission_ids": [9997, 9998, 9999]},
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No valid permissions found"}


def test_create_role_invalid_name_pattern(auth_headers):
    response = roles_post(json={"name": "invalid role name!"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_role_not_authorized():
    response = roles_post(json={"name": ROLE_A})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 PUT /{role_id}
# =========================================================

def test_update_role(auth_headers, test_role_with_permissions_and_authentication):
    role = test_role_with_permissions_and_authentication
    response = roles_put(str(role.id), json={"name": "updated_role"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "updated_role"


def test_update_role_not_found(auth_headers):
    response = roles_put("9999", json={"name": "non_existent_role"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Role not found"}


def test_update_role_duplicate(auth_headers, test_role):
    """test_role crea 'admin', intentar renombrarlo a 'manager' debe fallar."""
    response = roles_put(str(test_role.id), json={"name": "manager"}, headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Role name already exists"}


def test_update_role_invalid_permission_ids(auth_headers, test_role_with_permissions_and_authentication):
    role = test_role_with_permissions_and_authentication
    response = roles_put(str(role.id), json={"permission_ids": [9999, 8888]}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No valid permissions found"}


def test_update_role_valid_and_invalid_permission_ids(auth_headers, test_role_with_permissions_and_authentication, make_permission):
    role = test_role_with_permissions_and_authentication
    perm = make_permission(PERM_EXTRA)
    response = roles_put(str(role.id), json={"permission_ids": [perm.id, 9999]}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Permissions not found: [9999]"}


def test_update_role_valid_permission_ids(auth_headers, test_role_with_permissions_and_authentication, make_permission):
    role = test_role_with_permissions_and_authentication
    perm = make_permission(PERM_EXTRA)
    response = roles_put(str(role.id), json={"permission_ids": [perm.id]}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(p["name"] == PERM_EXTRA for p in data["permissions"])


def test_update_role_no_fields(auth_headers, test_role_with_permissions_and_authentication):
    role = test_role_with_permissions_and_authentication
    response = roles_put(str(role.id), json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "manager"


def test_update_role_not_authorized(test_role_with_permissions_and_authentication):
    role = test_role_with_permissions_and_authentication
    response = roles_put(str(role.id), json={"name": "hacked"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 DELETE /{role_id}
# =========================================================

def test_delete_role(auth_headers, test_role):
    """Eliminar 'admin' (test_role) — no es el rol del usuario autenticado."""
    response = roles_delete(str(test_role.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_role_not_found(auth_headers):
    response = roles_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Role not found"}


def test_delete_role_verify_gone(auth_headers, test_role):
    roles_delete(str(test_role.id), headers=auth_headers)
    response = roles_get(str(test_role.id), headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_role_not_authorized(test_role):
    response = roles_delete(str(test_role.id))
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)