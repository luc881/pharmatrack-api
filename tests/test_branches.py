from pharmatrack.api.routes.branches import get_db as original_get_db
from fastapi import status
from .utils import override_get_db, app, client, route_client_factory

app.dependency_overrides[original_get_db] = override_get_db
branches_get, branches_post, branches_put, branches_patch, branches_delete = route_client_factory(client, "branches")


# =========================================================
# 🔹 GET /
# Branches devuelve lista directa (sin paginación)
# =========================================================

def test_read_all_empty(auth_headers):
    """auth_headers crea una branch — debe haber al menos 1."""
    response = branches_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_read_all_with_data(auth_headers, test_branch):
    """test_branch crea 'Main Branch' — debe aparecer en la lista."""
    response = branches_get(headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    ids = [b["id"] for b in data]
    assert test_branch.id in ids


# =========================================================
# 🔹 GET /{branch_id}
# =========================================================

def test_read_branch_by_id(auth_headers, test_branch):
    response = branches_get(str(test_branch.id), headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_branch.id
    assert data["name"] == "Main Branch"


def test_read_branch_by_id_not_found(auth_headers):
    response = branches_get("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Branch not found"


# =========================================================
# 🔹 GET /{branch_id}/users
# =========================================================

def test_read_users_by_branch_id(auth_headers, test_user_with_role_permissions_branch_auth):
    user = test_user_with_role_permissions_branch_auth
    response = branches_get(f"{user.branch_id}/users", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["users"]) > 0
    assert all(u["branch_id"] == user.branch_id for u in data["users"])


def test_read_users_by_branch_id_not_found(auth_headers):
    response = branches_get("9999/users", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Branch not found"


# =========================================================
# 🔹 POST /
# =========================================================

def test_create_branch(auth_headers):
    """Usar nombre que no colisione con el branch del fixture auth."""
    new_branch = {
        "name": "New Test Branch",
        "address": "456 New St, City, Country"
    }
    response = branches_post(json=new_branch, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Test Branch"
    assert data["address"] == "456 New St, City, Country"


def test_create_branch_duplicate(auth_headers, test_branch):
    """test_branch ya creó 'Main Branch'."""
    new_branch = {
        "name": "Main Branch",
        "address": "123 Main St, City, Country"
    }
    response = branches_post(json=new_branch, headers=auth_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Branch already exists"


def test_create_branch_missing_name(auth_headers):
    response = branches_post(json={"address": "123 Main St"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_branch_not_authorized():
    response = branches_post(json={"name": "Branch", "address": "123 St"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 PUT /{branch_id}
# =========================================================

def test_update_branch(auth_headers, test_branch):
    updated = {
        "name": "Updated Branch",
        "address": "456 Updated St, City, Country"
    }
    response = branches_put(str(test_branch.id), json=updated, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Branch"
    assert data["address"] == "456 Updated St, City, Country"


def test_update_branch_not_found(auth_headers):
    updated = {"name": "Nonexistent Branch", "address": "789 Nonexistent St"}
    response = branches_put("9999", json=updated, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Branch not found"


def test_update_branch_not_authorized(test_branch):
    updated = {"name": "Hacked Branch", "address": "000 St"}
    response = branches_put(str(test_branch.id), json=updated)
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 DELETE /{branch_id}
# =========================================================

def test_delete_branch(auth_headers, test_branch):
    response = branches_delete(str(test_branch.id), headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_branch_verify_gone(auth_headers, test_branch):
    branches_delete(str(test_branch.id), headers=auth_headers)
    response = branches_get(str(test_branch.id), headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_branch_not_found(auth_headers):
    response = branches_delete("9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Branch not found"


def test_delete_branch_not_authorized(test_branch):
    response = branches_delete(str(test_branch.id))
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)