from pharmatrack.api.routes.permissions import get_db as original_get_db
from fastapi import status
from .utils import override_get_db, app, client, route_client_factory

app.dependency_overrides[original_get_db] = override_get_db
permissions_get, permissions_post, permissions_put, permissions_patch, permissions_delete = route_client_factory(client, "permissions")

# Nombres que NO usa el fixture test_role_with_permissions_and_authentication
# para evitar UniqueViolation al crear permisos en los tests
PERM_A = "reports.read"
PERM_B = "reports.create"
PERM_C = "reports.update"


# =========================================================
# 🔹 GET /
# =========================================================

def test_read_all_empty(auth_headers):
    """auth_headers ya crea ~80 permisos — verifica estructura paginada."""
    response = permissions_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert isinstance(data["data"], list)


def test_read_all_with_data(auth_headers, make_permission):
    """Verifica que los permisos creados existen y el total aumenta."""
    response_before = permissions_get(headers=auth_headers)
    total_before = response_before.json()["total"]

    perm_a = make_permission(PERM_A)
    perm_b = make_permission(PERM_B)

    # Verificar por ID que existen
    r_a = permissions_get(str(perm_a.id), headers=auth_headers)
    assert r_a.status_code == status.HTTP_200_OK
    assert r_a.json()["name"] == PERM_A

    r_b = permissions_get(str(perm_b.id), headers=auth_headers)
    assert r_b.status_code == status.HTTP_200_OK
    assert r_b.json()["name"] == PERM_B

    # Verificar que el total aumentó
    response_after = permissions_get(headers=auth_headers)
    assert response_after.json()["total"] == total_before + 2


def test_read_all_pagination(auth_headers, make_permission):
    """Verifica que page y page_size funcionan."""
    make_permission(PERM_A)
    make_permission(PERM_B)
    make_permission(PERM_C)
    response = permissions_get(params={"page": 1, "page_size": 2}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total"] >= 3
    assert data["total_pages"] >= 2


# =========================================================
# 🔹 GET /{permission_id}
# =========================================================

def test_read_permission_by_id(auth_headers, make_permission):
    perm = make_permission(PERM_A)
    response = permissions_get(str(perm.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == PERM_A
    assert data["id"] == perm.id


def test_read_permission_by_id_not_found(auth_headers):
    response = permissions_get("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Permission not found"}


# =========================================================
# 🔹 GET /{permission_id}/with-roles
# =========================================================

def test_read_permission_with_roles(auth_headers, test_role_with_permissions_and_authentication):
    """users.read ya existe en el rol creado por el fixture de auth."""
    role = test_role_with_permissions_and_authentication
    perm = next(p for p in role.permissions if p.name == "users.read")
    response = permissions_get(f"{perm.id}/with-roles", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    role_names = [r["name"] for r in data["roles"]]
    assert "manager" in role_names


def test_read_permission_with_roles_no_roles(auth_headers, make_permission):
    perm = make_permission(PERM_A)
    response = permissions_get(f"{perm.id}/with-roles", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["roles"] == []


def test_read_permission_with_roles_not_found(auth_headers):
    response = permissions_get("9999/with-roles", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Permission not found"}


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_permission(auth_headers):
    response = permissions_post(json={"name": PERM_A}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == PERM_A
    assert "id" in data


def test_create_permission_strip_lowercase(auth_headers):
    response = permissions_post(json={"name": "  CREATE.Reports  "}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "create.reports"


def test_create_permission_invalid_pattern(auth_headers):
    response = permissions_post(json={"name": "Invalid_Permission1"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"][0]["msg"] == "Value error, Invalid permission name pattern, only lowercase letters and '.' are allowed"


def test_create_permission_duplicate(auth_headers):
    """users.read ya existe gracias al fixture auth_headers."""
    response = permissions_post(json={"name": "users.read"}, headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Permission already exists"}


def test_create_permission_missing_name(auth_headers):
    response = permissions_post(json={}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_permission_empty_name(auth_headers):
    response = permissions_post(json={"name": ""}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_permission_not_authorized():
    response = permissions_post(json={"name": PERM_A})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 PUT /{permission_id}
# =========================================================

def test_update_permission(auth_headers, make_permission):
    perm = make_permission(PERM_A)
    response = permissions_put(str(perm.id), json={"name": PERM_B}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == PERM_B
    assert data["id"] == perm.id


def test_update_permission_not_found(auth_headers):
    response = permissions_put("9999", json={"name": PERM_A}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Permission not found"}


def test_update_permission_duplicate(auth_headers, make_permission):
    """Renombrar PERM_A a users.read debe fallar — users.read ya existe."""
    perm = make_permission(PERM_A)
    response = permissions_put(str(perm.id), json={"name": "users.read"}, headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Permission name already exists"}


def test_update_permission_invalid_pattern(auth_headers, make_permission):
    perm = make_permission(PERM_A)
    response = permissions_put(str(perm.id), json={"name": "Invalid_Name"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_permission_not_authorized(make_permission):
    perm = make_permission(PERM_A)
    response = permissions_put(str(perm.id), json={"name": PERM_B})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 DELETE /{permission_id}
# =========================================================

def test_delete_permission(auth_headers, make_permission):
    perm = make_permission(PERM_A)
    response = permissions_delete(str(perm.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_permission_not_found(auth_headers):
    response = permissions_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Permission not found"}


def test_delete_permission_not_authorized(make_permission):
    perm = make_permission(PERM_A)
    response = permissions_delete(str(perm.id))
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_delete_permission_verify_gone(auth_headers, make_permission):
    perm = make_permission(PERM_A)
    permissions_delete(str(perm.id), headers=auth_headers)
    response = permissions_get(str(perm.id), headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND