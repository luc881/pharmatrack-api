"""Cuentas de cliente (login con Google) y pedidos del sitio publico."""
import pytest

from .utils import client
from .test_animals import _make_taxonomy, _create_animal

GOOGLE_PROFILE = {
    "sub": "google-123",
    "email": "cliente@example.com",
    "name": "Cliente Prueba",
    "picture": "https://example.com/foto.jpg",
}


@pytest.fixture
def fake_google(monkeypatch):
    """Evita la llamada real a Google: el token "ok" devuelve el perfil."""
    def _verify(id_token: str):
        if id_token != "ok":
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Google sign-in failed.")
        return dict(GOOGLE_PROFILE)

    monkeypatch.setattr("pharmatrack.api.routes.shop.verify_google_id_token", _verify)


def _sign_in() -> dict:
    res = client.post("/api/v1/shop/auth/google", json={"id_token": "ok"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# =========================================================
# Login
# =========================================================
def test_google_sign_in_creates_customer_once(fake_google):
    res = client.post("/api/v1/shop/auth/google", json={"id_token": "ok"})
    assert res.status_code == 200, res.text
    first = res.json()["customer"]
    assert first["email"] == GOOGLE_PROFILE["email"]
    assert first["name"] == GOOGLE_PROFILE["name"]

    # entrar de nuevo reusa la misma cuenta, no crea otra
    again = client.post("/api/v1/shop/auth/google", json={"id_token": "ok"}).json()["customer"]
    assert again["id"] == first["id"]


def test_bad_google_token_is_rejected(fake_google):
    assert client.post("/api/v1/shop/auth/google", json={"id_token": "nope"}).status_code == 401


def test_customer_token_cannot_touch_the_dashboard(fake_google):
    """Lo importante: un cliente de la tienda NO es un usuario del sistema."""
    headers = _sign_in()
    for url in ("/api/v1/users", "/api/v1/animals", "/api/v1/orders"):
        assert client.get(url, headers=headers).status_code == 401, url


def test_staff_token_cannot_use_customer_endpoints(auth_headers):
    assert client.get("/api/v1/shop/me", headers=auth_headers).status_code == 401


def test_me_requires_auth():
    assert client.get("/api/v1/shop/me").status_code == 401


# =========================================================
# Favoritos y carrito
# =========================================================
def test_favorites_and_cart_roundtrip(fake_google):
    headers = _sign_in()

    res = client.put("/api/v1/shop/me", headers=headers,
                     json={"favorites": ["s1", "m4"], "phone": "5512345678"})
    assert res.status_code == 200, res.text
    assert res.json()["favorites"] == ["s1", "m4"]

    # guardar solo el carrito no borra los favoritos (update parcial)
    cart = [{"key": "pr-1", "title": "Sustrato", "qty": 2, "price": 90}]
    res = client.put("/api/v1/shop/me", headers=headers, json={"cart": cart})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cart"] == cart
    assert body["favorites"] == ["s1", "m4"]
    assert body["phone"] == "5512345678"

    assert client.get("/api/v1/shop/me", headers=headers).json()["cart"] == cart


# =========================================================
# Pedidos
# =========================================================
def test_order_price_comes_from_the_catalog(fake_google, auth_headers):
    _group, _sub, _genus, sp, morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]], price=3500.0)
    headers = _sign_in()

    # el cliente manda un precio ridiculo: debe ignorarse por completo
    res = client.post("/api/v1/shop/orders", headers=headers, json={
        "items": [{"key": f"m{morph['id']}-u", "qty": 2, "price": 1}],
        "contact_phone": "5512345678",
    })
    assert res.status_code == 201, res.text
    order = res.json()
    assert order["items"][0]["unit_price"] == 3500.0
    assert order["total"] == 7000.0
    assert order["status"] == "pending"

    # aparece en "mis pedidos"
    mine = client.get("/api/v1/shop/orders", headers=headers).json()
    assert [o["id"] for o in mine] == [order["id"]]


def test_order_uses_price_tier_when_asked(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=100.0)
    client.put(f"/api/v1/species/{sp['id']}", headers=auth_headers,
               json={"price_tiers": [{"quantity": 6, "price": 450}]})
    headers = _sign_in()

    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": f"s{sp['id']}-6", "qty": 1}]})
    assert res.status_code == 201, res.text
    item = res.json()["items"][0]
    assert item["unit_price"] == 450.0
    assert item["detail"] == "Paquete de 6"

    # una escala que no existe no se puede pedir
    bad = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": f"s{sp['id']}-99", "qty": 1}]})
    assert bad.status_code == 409


def test_cannot_order_from_a_hidden_group(fake_google, auth_headers):
    group, _sub, _genus, sp, morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]])
    client.put(f"/api/v1/animal-groups/{group['id']}",
               json={"show_public": False}, headers=auth_headers)
    headers = _sign_in()

    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": f"m{morph['id']}-u", "qty": 1}]})
    assert res.status_code == 409, res.text


def test_unknown_item_key_is_rejected(fake_google):
    headers = _sign_in()
    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": "drop-table", "qty": 1}]})
    assert res.status_code == 422


def test_orders_are_private_to_their_customer(fake_google, auth_headers, monkeypatch):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()
    client.post("/api/v1/shop/orders", headers=headers,
                json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}]})

    # otro cliente entra: no ve pedidos ajenos
    monkeypatch.setattr(
        "pharmatrack.api.routes.shop.verify_google_id_token",
        lambda _t: {"sub": "google-999", "email": "otro@example.com",
                    "name": "Otro", "picture": None},
    )
    other = _sign_in()
    assert client.get("/api/v1/shop/orders", headers=other).json() == []


# =========================================================
# Pedidos en el dashboard
# =========================================================
def test_admin_sees_orders_and_changes_status(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}]}).json()

    listing = client.get("/api/v1/orders", headers=auth_headers)
    assert listing.status_code == 200, listing.text
    row = listing.json()["data"][0]
    assert row["id"] == order["id"]
    assert row["customer_email"] == GOOGLE_PROFILE["email"]

    res = client.put(f"/api/v1/orders/{order['id']}", headers=auth_headers,
                     json={"status": "confirmed"})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "confirmed"

    # el cliente ve el nuevo estado
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "confirmed"

    assert client.put(f"/api/v1/orders/{order['id']}", headers=auth_headers,
                      json={"status": "inventado"}).status_code == 422


def test_admin_orders_require_auth():
    assert client.get("/api/v1/orders").status_code == 401
