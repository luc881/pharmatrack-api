"""Regresiones de la auditoría de seguridad."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from pharmatrack.utils.security import hash_token

from .utils import client


def test_sale_cannot_be_completed_via_put(auth_headers, test_sale):
    # Completar por PUT saltaría el descuento de stock: solo por /complete
    res = client.put(f"/api/v1/sales/{test_sale.id}", json={"status": "completed"}, headers=auth_headers)
    assert res.status_code == 400
    # cancelar un borrador sigue permitido
    res = client.put(f"/api/v1/sales/{test_sale.id}", json={"status": "cancelled"}, headers=auth_headers)
    assert res.status_code == 200, res.text


def _reset_token(db_session, user):
    from pharmatrack.models.password_reset_tokens.orm import PasswordResetToken

    tok = PasswordResetToken(token=hash_token("tok-123"), user_id=user.id, used=False,
                             expires_at=datetime.now(timezone.utc) + timedelta(minutes=15))
    db_session.add(tok)
    db_session.commit()
    return tok


def test_reset_password_enforces_rules_and_revokes_sessions(db_session, test_user_with_role_permissions_branch_auth):
    user = test_user_with_role_permissions_branch_auth
    user.remember_token = hash_token("old-refresh")
    db_session.commit()
    _reset_token(db_session, user)

    weak = client.post("/api/v1/auth/reset-password", json={"token": "tok-123", "new_password": "a"})
    assert weak.status_code == 422

    ok = client.post("/api/v1/auth/reset-password", json={"token": "tok-123", "new_password": "NuevaClave123"})
    assert ok.status_code == 200, ok.text
    # la sesión abierta con la contraseña vieja ya no renueva
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "old-refresh"}).status_code == 401


def test_deleted_user_cannot_refresh(db_session, test_user_with_role_permissions_branch_auth):
    user = test_user_with_role_permissions_branch_auth
    user.remember_token = hash_token("live-refresh")
    user.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    db_session.commit()
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "live-refresh"}).status_code == 200

    user.deleted_at = datetime.now(timezone.utc)
    db_session.commit()
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "live-refresh"}).status_code == 401


def test_order_email_escapes_customer_fields():
    from pharmatrack.utils.email import _contact_html

    order = SimpleNamespace(contact_name='<a href="http://evil">Pagar aquí</a>', contact_phone="55<b>",
                            address="<img src=x>", notes="<script>x</script>")
    html = _contact_html(order, SimpleNamespace(name=None, email="a@b.com"), with_address=True)
    assert "<a href" not in html and "<script>" not in html and "<img" not in html
    assert "&lt;a href=" in html


def test_tokens_stored_hashed(db_session, test_user_with_role_permissions_branch_auth):
    """Login y reset guardan el sha256, nunca el token en claro."""
    from pharmatrack.models.password_reset_tokens.orm import PasswordResetToken
    from .utils import client as c

    user = test_user_with_role_permissions_branch_auth
    login = c.post("/api/v1/auth/token", data={"username": user.email, "password": "secureMpassword123"})
    assert login.status_code == 200, login.text
    refresh = login.json()["refresh_token"]
    db_session.refresh(user)
    assert user.remember_token == hash_token(refresh) and user.remember_token != refresh
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 200
    # el hash guardado no sirve como token
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": user.remember_token}).status_code == 401

    c.post("/api/v1/auth/forgot-password", json={"email": user.email})
    stored = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).all()
    assert stored and all(len(t.token) == 64 for t in stored)
