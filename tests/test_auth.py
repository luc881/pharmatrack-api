from pharmatrack.api.routes.auth import get_db as original_get_db
from fastapi import status
from .utils import override_get_db, app, client, route_client_factory

app.dependency_overrides[original_get_db] = override_get_db
auth_get, auth_post, auth_put, auth_patch, auth_delete = route_client_factory(client, "auth")


# =========================================================
# 🔹 POST /token  (login)
# =========================================================

def test_login_success(test_user_with_role_permissions_branch_auth):
    response = auth_post("token", data={
        "username": test_user_with_role_permissions_branch_auth.email,
        "password": "secureMpassword123"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password(test_user_with_role_permissions_branch_auth):
    response = auth_post("token", data={
        "username": test_user_with_role_permissions_branch_auth.email,
        "password": "wrongpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_wrong_email(test_user_with_role_permissions_branch_auth):
    response = auth_post("token", data={
        "username": "nonexistent@example.com",
        "password": "secureMpassword123"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_missing_fields():
    response = auth_post("token", data={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_returns_valid_token(test_user_with_role_permissions_branch_auth):
    """El token obtenido permite acceder a endpoints protegidos."""
    login = auth_post("token", data={
        "username": test_user_with_role_permissions_branch_auth.email,
        "password": "secureMpassword123"
    })
    token = login.json()["access_token"]

    # Verificar que el token funciona en un endpoint protegido
    users_get, *_ = route_client_factory(client, "users")
    response = users_get(headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK


# =========================================================
# 🔹 POST /refresh  (renovar access token)
# =========================================================

def test_refresh_token_success(test_user_with_role_permissions_branch_auth):
    # Primero hacer login para obtener refresh token
    login = auth_post("token", data={
        "username": test_user_with_role_permissions_branch_auth.email,
        "password": "secureMpassword123"
    })
    refresh_token = login.json()["refresh_token"]

    response = auth_post("refresh", json={"refresh_token": refresh_token})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid():
    response = auth_post("refresh", json={"refresh_token": "invalid_token_xyz"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_refresh_token_missing():
    response = auth_post("refresh", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =========================================================
# 🔹 POST /logout
# =========================================================

def test_logout_success(test_user_with_role_permissions_branch_auth, auth_headers):
    # Obtener refresh token
    login = auth_post("token", data={
        "username": test_user_with_role_permissions_branch_auth.email,
        "password": "secureMpassword123"
    })
    refresh_token = login.json()["refresh_token"]

    response = auth_post("logout", json={"refresh_token": refresh_token}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


def test_logout_invalidates_refresh_token(test_user_with_role_permissions_branch_auth, auth_headers):
    """Después del logout, el refresh token no debe funcionar."""
    login = auth_post("token", data={
        "username": test_user_with_role_permissions_branch_auth.email,
        "password": "secureMpassword123"
    })
    refresh_token = login.json()["refresh_token"]

    # Logout
    auth_post("logout", json={"refresh_token": refresh_token}, headers=auth_headers)

    # Intentar usar el refresh token — debe fallar
    response = auth_post("refresh", json={"refresh_token": refresh_token})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_logout_not_authorized():
    """Logout sin token de acceso debe fallar."""
    response = auth_post("logout", json={"refresh_token": "any_token"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# =========================================================
# 🔹 Acceso con token inválido
# =========================================================

def test_access_with_invalid_token():
    users_get, *_ = route_client_factory(client, "users")
    response = users_get(headers={"Authorization": "Bearer token_invalido"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_access_without_token():
    users_get, *_ = route_client_factory(client, "users")
    response = users_get()
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)