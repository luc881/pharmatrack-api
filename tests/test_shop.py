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


def test_identical_pending_order_is_rejected(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()
    payload = {"items": [{"key": f"s{sp['id']}-u", "qty": 1}]}

    first = client.post("/api/v1/shop/orders", headers=headers, json=payload)
    assert first.status_code == 201

    dup = client.post("/api/v1/shop/orders", headers=headers, json=payload)
    assert dup.status_code == 409
    assert first.json()["code"] in dup.json()["detail"]

    # con otra cantidad ya no es duplicado
    other = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 2}]})
    assert other.status_code == 201, other.text

    # y si el pendiente se confirma, el mismo contenido vuelve a ser válido
    client.put(f"/api/v1/orders/{first.json()['id']}", headers=auth_headers,
               json={"status": "confirmed"})
    again = client.post("/api/v1/shop/orders", headers=headers, json=payload)
    assert again.status_code == 201, again.text


def test_pending_orders_are_capped(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()

    # 3 pedidos pendientes distintos (cantidades diferentes)
    for qty in (1, 2, 3):
        res = client.post("/api/v1/shop/orders", headers=headers,
                          json={"items": [{"key": f"s{sp['id']}-u", "qty": qty}]})
        assert res.status_code == 201, res.text

    # el cuarto se rechaza aunque sea distinto
    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": f"s{sp['id']}-u", "qty": 4}]})
    assert res.status_code == 409
    assert "pendientes" in res.json()["detail"]

    # atender uno libera el cupo
    first_id = client.get("/api/v1/shop/orders", headers=headers).json()[-1]["id"]
    client.put(f"/api/v1/orders/{first_id}", headers=auth_headers,
               json={"status": "cancelled"})
    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": f"s{sp['id']}-u", "qty": 4}]})
    assert res.status_code == 201, res.text


def test_customer_cancels_own_pending_order(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}]}).json()

    res = client.delete(f"/api/v1/shop/orders/{order['id']}", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "cancelled"

    # cancelar libera el candado de duplicado: puede volver a pedir lo mismo
    again = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}]})
    assert again.status_code == 201, again.text


def test_customer_cannot_cancel_foreign_or_confirmed(fake_google, auth_headers, monkeypatch):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}]}).json()

    # otro cliente no puede cancelarlo (ni saber que existe: 404)
    monkeypatch.setattr(
        "pharmatrack.api.routes.shop.verify_google_id_token",
        lambda _t: {"sub": "google-999", "email": "otro@example.com",
                    "name": "Otro", "picture": None},
    )
    other = _sign_in()
    assert client.delete(f"/api/v1/shop/orders/{order['id']}", headers=other).status_code == 404

    # confirmado ya no se cancela desde la cuenta
    client.put(f"/api/v1/orders/{order['id']}", headers=auth_headers,
               json={"status": "confirmed"})
    res = client.delete(f"/api/v1/shop/orders/{order['id']}", headers=headers)
    assert res.status_code == 409
    assert "WhatsApp" in res.json()["detail"]


def test_daily_creation_cap_stops_create_cancel_loop(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    headers = _sign_in()
    payload = {"items": [{"key": f"s{sp['id']}-u", "qty": 1}]}

    # crear→cancelar en bucle: el tope de pendientes no lo frena…
    for _ in range(10):
        res = client.post("/api/v1/shop/orders", headers=headers, json=payload)
        assert res.status_code == 201, res.text
        client.delete(f"/api/v1/shop/orders/{res.json()['id']}", headers=headers)

    # …pero el tope diario sí
    res = client.post("/api/v1/shop/orders", headers=headers, json=payload)
    assert res.status_code == 409
    assert "24 horas" in res.json()["detail"]


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


def test_shipping_can_be_turned_off(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    items = [{"key": f"s{sp['id']}-u", "qty": 1}]

    # con envíos apagados, la API los rechaza aunque el sitio los ofreciera
    client.put("/api/v1/settings/site", headers=auth_headers,
               json={"show_category_browse": True, "shipping_enabled": False})
    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": items, "delivery_method": "shipping"})
    assert res.status_code == 409
    assert "CDMX" in res.json()["detail"]

    # la entrega personal sigue funcionando
    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": items, "delivery_method": "pickup",
                            "contact_phone": "5512345678"})
    assert res.status_code == 201, res.text

    # y al reactivarlos vuelve a pasar
    client.put("/api/v1/settings/site", headers=auth_headers,
               json={"show_category_browse": True, "shipping_enabled": True})
    res = client.post("/api/v1/shop/orders", headers=headers,
                      json={"items": [{"key": f"s{sp['id']}-u", "qty": 2}],
                            "delivery_method": "shipping"})
    assert res.status_code == 201, res.text


# =========================================================
# Stock: barrera dura solo al pagar (checkout) + validación del carrito
# =========================================================
def test_checkout_blocked_when_over_stock(fake_google, auth_headers):
    _g, _s, _ge, sp, _m = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)  # 1 disponible
    headers = _sign_in()
    # pedir de más es válido (es una solicitud); pagar de más no
    order = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 2}],
                              "delivery_method": "pickup",
                              "contact_phone": "5512345678"}).json()
    res = client.post(f"/api/v1/shop/orders/{order['id']}/checkout", headers=headers)
    assert res.status_code == 409, res.text
    assert "Solo quedan 1" in res.json()["detail"]


def test_confirmed_order_reserves_stock_from_checkout(fake_google, auth_headers):
    _g, _s, _ge, sp, _m = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    _create_animal(auth_headers, sp["id"], price=250.0)  # 2 disponibles
    headers = _sign_in()
    pickup = {"delivery_method": "pickup", "contact_phone": "5512345678"}

    first = client.post("/api/v1/shop/orders", headers=headers,
                        json={"items": [{"key": f"s{sp['id']}-u", "qty": 2}], **pickup}).json()
    # staff lo confirma: sus 2 unidades quedan apartadas
    client.put(f"/api/v1/orders/{first['id']}", headers=auth_headers,
               json={"status": "confirmed"})

    # otro pedido ya no tiene stock para pagar (2 físico − 2 apartado = 0)
    second = client.post("/api/v1/shop/orders", headers=headers,
                         json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}], **pickup}).json()
    res = client.post(f"/api/v1/shop/orders/{second['id']}/checkout", headers=headers)
    assert res.status_code == 409, res.text
    assert "ya no está disponible" in res.json()["detail"]


def test_validate_cart_reports_availability(fake_google, auth_headers):
    _g, _s, _ge, sp, morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]], price=250.0)  # 1

    res = client.post("/api/v1/shop/cart/validate", json={"items": [
        {"key": f"m{morph['id']}-u", "qty": 5},
        {"key": "pr-999999", "qty": 1},
    ]})
    assert res.status_code == 200, res.text
    items = {i["key"]: i for i in res.json()["items"]}
    assert items[f"m{morph['id']}-u"]["available"] is True
    assert items[f"m{morph['id']}-u"]["max_qty"] == 1
    assert items["pr-999999"]["available"] is False


def test_checkout_hold_reserves_then_expires(fake_google, auth_headers, db_session, monkeypatch):
    from datetime import datetime, timezone, timedelta
    from pharmatrack.models.customers.orm import Order
    from pharmatrack.api.routes.shop import CHECKOUT_HOLD_MINUTES

    monkeypatch.setattr("pharmatrack.api.routes.shop.create_preference",
                        lambda *_a, **_k: ("pref", "https://mp.test/pagar"))
    _g, _s, _ge, sp, _m = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    _create_animal(auth_headers, sp["id"], price=250.0)  # 2 disponibles
    headers = _sign_in()
    pickup = {"delivery_method": "pickup", "contact_phone": "5512345678"}

    a = client.post("/api/v1/shop/orders", headers=headers,
                    json={"items": [{"key": f"s{sp['id']}-u", "qty": 2}], **pickup}).json()
    # A abre el pago: aparta las 2 unidades
    assert client.post(f"/api/v1/shop/orders/{a['id']}/checkout",
                       headers=headers).status_code == 200

    b = client.post("/api/v1/shop/orders", headers=headers,
                    json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}], **pickup}).json()
    # B no puede pagar mientras A tiene el stock apartado
    blocked = client.post(f"/api/v1/shop/orders/{b['id']}/checkout", headers=headers)
    assert blocked.status_code == 409, blocked.text

    # cae la reserva de A al pasar el TTL: B ya puede pagar
    db_session.expire_all()
    order_a = db_session.get(Order, a["id"])
    order_a.checkout_at = (
        datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=CHECKOUT_HOLD_MINUTES + 5)
    )
    db_session.commit()
    freed = client.post(f"/api/v1/shop/orders/{b['id']}/checkout", headers=headers)
    assert freed.status_code == 200, freed.text


# =========================================================
# Cuentas que abusan
# =========================================================
def test_blocked_customer_cannot_order_until_unblocked(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    body = {"items": [{"key": f"s{sp['id']}-u", "qty": 1}],
            "delivery_method": "pickup", "contact_phone": "5512345678"}
    first = client.post("/api/v1/shop/orders", headers=headers, json=body)
    assert first.status_code == 201, first.text

    listed = client.get("/api/v1/orders", headers=auth_headers).json()["data"][0]
    assert listed["customer_blocked"] is False
    url = f"/api/v1/orders/customers/{listed['customer_id']}/block"
    assert client.put(url, headers=auth_headers, json={"blocked": True}).status_code == 200

    body["items"][0]["qty"] = 2
    res = client.post("/api/v1/shop/orders", headers=headers, json=body)
    assert res.status_code == 403
    # sigue pudiendo entrar y ver lo que ya pidió
    assert len(client.get("/api/v1/shop/orders", headers=headers).json()) == 1
    assert client.get("/api/v1/orders", headers=auth_headers).json()["data"][0]["customer_blocked"] is True

    client.put(url, headers=auth_headers, json={"blocked": False})
    assert client.post("/api/v1/shop/orders", headers=headers, json=body).status_code == 201


def test_order_text_is_capped(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    res = client.post("/api/v1/shop/orders", headers=_sign_in(), json={
        "items": [{"key": f"s{sp['id']}-u", "qty": 1}],
        "delivery_method": "shipping", "notes": "x" * 1001})
    assert res.status_code == 422


# =========================================================
# Eliminar cuenta, pendientes que caducan, tope por red
# =========================================================
def test_delete_account_scrubs_personal_data(fake_google, auth_headers):
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    client.put("/api/v1/shop/me", headers=headers, json={"phone": "5512345678", "street": "Calle 1"})
    order = client.post("/api/v1/shop/orders", headers=headers, json={
        "items": [{"key": f"s{sp['id']}-u", "qty": 1}], "delivery_method": "pickup",
        "contact_phone": "5512345678", "notes": "tocar el timbre"}).json()

    assert client.delete("/api/v1/shop/me", headers=headers).status_code == 204
    # el token viejo ya no entra
    assert client.get("/api/v1/shop/me", headers=headers).status_code == 401

    kept = client.get(f"/api/v1/orders/{order['id']}", headers=auth_headers).json()
    assert kept["status"] == "cancelled" and kept["total"] == 250.0
    assert kept["contact_phone"] is None and kept["notes"] is None
    assert kept["customer_name"] is None and GOOGLE_PROFILE["email"] not in kept["customer_email"]

    # volver a entrar con Google abre una cuenta nueva, vacía
    again = client.get("/api/v1/shop/me", headers=_sign_in()).json()
    assert again["phone"] is None and again["id"] != kept["customer_id"]


def test_cannot_delete_account_with_order_in_progress(fake_google, auth_headers, db_session):
    from pharmatrack.models.customers.orm import Order
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers, json={
        "items": [{"key": f"s{sp['id']}-u", "qty": 1}], "delivery_method": "pickup",
        "contact_phone": "5512345678"}).json()
    db_session.query(Order).filter(Order.id == order["id"]).update({"status": "paid"})
    db_session.commit()
    assert client.delete("/api/v1/shop/me", headers=headers).status_code == 409


def test_stale_pending_orders_expire(fake_google, auth_headers, db_session):
    from datetime import datetime, timedelta
    from pharmatrack.models.customers.orm import Order
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers, json={
        "items": [{"key": f"s{sp['id']}-u", "qty": 1}], "delivery_method": "pickup",
        "contact_phone": "5512345678"}).json()
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "pending"

    db_session.query(Order).filter(Order.id == order["id"]).update(
        {"created_at": datetime.utcnow() - timedelta(days=15)})
    db_session.commit()
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "cancelled"


def test_daily_cap_per_network_needs_the_site_secret(fake_google, auth_headers, monkeypatch):
    from pharmatrack.api.routes import shop
    from pharmatrack.config import settings
    monkeypatch.setattr(settings, "shop_proxy_secret", "secreto-del-sitio")
    monkeypatch.setattr(shop, "MAX_ORDERS_PER_DAY_PER_IP", 1)
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    body = {"items": [{"key": f"s{sp['id']}-u", "qty": 1}], "delivery_method": "pickup",
            "contact_phone": "5512345678"}

    # una IP que no viene avalada por el sitio no cuenta (cualquiera la inventaría)
    forged = {**headers, "X-Client-IP": "203.0.113.9", "X-Proxy-Secret": "otro"}
    assert client.post("/api/v1/shop/orders", headers=forged, json=body).status_code == 201

    site = {**headers, "X-Client-IP": "203.0.113.9", "X-Proxy-Secret": "secreto-del-sitio"}
    body["items"][0]["qty"] = 2
    assert client.post("/api/v1/shop/orders", headers=site, json=body).status_code == 201
    body["items"][0]["qty"] = 3
    res = client.post("/api/v1/shop/orders", headers=site, json=body)
    assert res.status_code == 409 and "24 horas" in res.json()["detail"]
