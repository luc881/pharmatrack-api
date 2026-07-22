"""Pago en linea (Mercado Pago Checkout Pro) de pedidos de entrega personal."""
import pytest

from .utils import client
from .test_shop import fake_google, _sign_in  # noqa: F401
from .test_animals import _make_taxonomy, _create_animal


@pytest.fixture
def order_with_pickup(fake_google, auth_headers):  # noqa: F811
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers, json={
        "items": [{"key": f"s{sp['id']}-u", "qty": 1}],
        "delivery_method": "pickup",
    }).json()
    return headers, order


def _approved(order, amount=None, ref=None):
    return {
        "status": "approved",
        "external_reference": ref or order["code"],
        "transaction_amount": amount if amount is not None else order["total"],
    }


# =========================================================
# Inicio del pago
# =========================================================
def test_checkout_returns_payment_url(order_with_pickup, monkeypatch):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.create_preference",
                        lambda *_a, **_k: ("pref-1", "https://mp.test/pagar"))

    res = client.post(f"/api/v1/shop/orders/{order['id']}/checkout", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["payment_url"] == "https://mp.test/pagar"


def test_shipping_orders_cannot_pay_online(fake_google, auth_headers):  # noqa: F811
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=250.0)
    headers = _sign_in()
    order = client.post("/api/v1/shop/orders", headers=headers, json={
        "items": [{"key": f"s{sp['id']}-u", "qty": 1}],
        "delivery_method": "shipping",
    }).json()

    res = client.post(f"/api/v1/shop/orders/{order['id']}/checkout", headers=headers)
    assert res.status_code == 409
    assert "envío" in res.json()["detail"]


def test_cannot_start_checkout_of_someone_elses_order(order_with_pickup, monkeypatch):
    _headers, order = order_with_pickup
    monkeypatch.setattr(
        "pharmatrack.api.routes.shop.verify_google_id_token",
        lambda _t: {"sub": "google-999", "email": "otro@example.com",
                    "name": "Otro", "picture": None},
    )
    other = _sign_in()
    res = client.post(f"/api/v1/shop/orders/{order['id']}/checkout", headers=other)
    assert res.status_code == 404


# =========================================================
# Webhook — lo critico: no se puede falsificar un pago
# =========================================================
def test_webhook_marks_order_paid(order_with_pickup, monkeypatch):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))

    res = client.post("/api/v1/shop/payments/webhook",
                      json={"type": "payment", "data": {"id": "12345"}})
    assert res.status_code == 200, res.text

    mine = client.get("/api/v1/shop/orders", headers=headers).json()[0]
    assert mine["status"] == "paid"
    assert mine["payment_id"] == "12345"
    assert mine["paid_at"] is not None


def test_webhook_body_alone_cannot_mark_paid(order_with_pickup, monkeypatch):
    """El cuerpo del webhook es dato no confiable: si Mercado Pago no
    confirma el pago, el pedido NO se marca como pagado."""
    headers, order = order_with_pickup
    # Mercado Pago no conoce ese pago
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment", lambda _id: None)

    res = client.post("/api/v1/shop/payments/webhook", json={
        "type": "payment",
        "data": {"id": "99999"},
        # aunque el atacante mande todo esto, se ignora
        "status": "approved",
        "external_reference": order["code"],
        "transaction_amount": order["total"],
    })
    assert res.status_code == 200
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "pending"


def test_webhook_ignores_unapproved_and_short_payments(order_with_pickup, monkeypatch):
    headers, order = order_with_pickup

    # pago pendiente/rechazado no marca nada
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: {**_approved(order), "status": "rejected"})
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "1"}})
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "pending"

    # pago aprobado pero por menos del total tampoco
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order, amount=1))
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "2"}})
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "pending"


def test_sync_recovers_a_lost_webhook(order_with_pickup, monkeypatch):
    """Si el webhook nunca llegó, al volver de Mercado Pago el sitio
    reconcilia y el pedido no se queda pendiente con el dinero cobrado."""
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.find_approved_payment",
                        lambda _ref: {**_approved(order), "id": "654321"})

    res = client.post(f"/api/v1/shop/orders/{order['id']}/sync-payment", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "paid"
    assert res.json()["payment_id"] == "654321"


def test_sync_does_not_invent_payments(order_with_pickup, monkeypatch):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.find_approved_payment",
                        lambda _ref: None)
    res = client.post(f"/api/v1/shop/orders/{order['id']}/sync-payment", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "pending"


def test_webhook_is_idempotent(order_with_pickup, monkeypatch):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))

    for _ in range(3):
        assert client.post("/api/v1/shop/payments/webhook",
                           json={"data": {"id": "777"}}).status_code == 200

    mine = client.get("/api/v1/shop/orders", headers=headers).json()
    assert len(mine) == 1
    assert mine[0]["payment_id"] == "777"


def test_paid_order_cannot_be_cancelled_by_customer(order_with_pickup, monkeypatch):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "555"}})

    res = client.delete(f"/api/v1/shop/orders/{order['id']}", headers=headers)
    assert res.status_code == 409
    assert "pagado" in res.json()["detail"]


def test_webhook_without_payment_id_is_ignored():
    assert client.post("/api/v1/shop/payments/webhook", json={}).status_code == 200


# =========================================================
# Firma del webhook (capa previa, opcional)
# =========================================================
SECRET = "clave-de-prueba"


def _signature(data_id: str, request_id: str, ts: str = "1700000000") -> str:
    import hmac, hashlib
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    v1 = hmac.new(SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return f"ts={ts},v1={v1}"


@pytest.fixture
def signed(monkeypatch):
    from pharmatrack.utils import mercadopago
    monkeypatch.setattr(mercadopago.settings, "mercadopago_webhook_secret", SECRET)


def test_signature_is_optional_when_no_secret(order_with_pickup, monkeypatch):
    """Sin secreto configurado el webhook sigue funcionando: no se puede
    romper el cobro por no haber puesto una variable opcional."""
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "111"}})
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "paid"


def test_valid_signature_is_accepted(order_with_pickup, monkeypatch, signed):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))

    res = client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "222"}},
                      headers={"x-signature": _signature("222", "req-1"),
                               "x-request-id": "req-1"})
    assert res.status_code == 200
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "paid"


def test_bad_signature_is_dropped_before_calling_mercadopago(order_with_pickup,
                                                             monkeypatch, signed):
    headers, order = order_with_pickup
    called = []

    def _spy(payment_id):
        called.append(payment_id)
        return _approved(order)

    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment", _spy)

    # firma inventada
    res = client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "333"}},
                      headers={"x-signature": "ts=1700000000,v1=deadbeef",
                               "x-request-id": "req-2"})
    assert res.status_code == 200
    assert called == []  # ni siquiera se consultó a Mercado Pago
    assert client.get("/api/v1/shop/orders", headers=headers).json()[0]["status"] == "pending"

    # sin cabecera tampoco pasa
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "444"}})
    assert called == []


# =========================================================
# Revisión: guardas adicionales
# =========================================================
def test_double_payment_keeps_first_and_logs(order_with_pickup, monkeypatch):
    """Dos checkouts abiertos, dos pagos aprobados: se conserva el primero
    (el segundo se reembolsa a mano) y no se manda otro correo."""
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "aaa1"}})
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "bbb2"}})

    mine = client.get("/api/v1/shop/orders", headers=headers).json()[0]
    assert mine["payment_id"] == "aaa1"  # el segundo NO lo pisa


def test_admin_cannot_mark_paid_without_a_real_payment(order_with_pickup, auth_headers):
    _headers, order = order_with_pickup
    res = client.put(f"/api/v1/orders/{order['id']}", headers=auth_headers,
                     json={"status": "paid"})
    assert res.status_code == 409
    assert "Confirmado" in res.json()["detail"]


def test_admin_can_move_a_truly_paid_order(order_with_pickup, auth_headers, monkeypatch):
    headers, order = order_with_pickup
    monkeypatch.setattr("pharmatrack.api.routes.shop.get_payment",
                        lambda _id: _approved(order))
    client.post("/api/v1/shop/payments/webhook", json={"data": {"id": "ccc3"}})

    # pagado -> confirmado (y de vuelta a paid, ahora sí con pago real)
    assert client.put(f"/api/v1/orders/{order['id']}", headers=auth_headers,
                      json={"status": "confirmed"}).status_code == 200
    assert client.put(f"/api/v1/orders/{order['id']}", headers=auth_headers,
                      json={"status": "paid"}).status_code == 200


def test_webhook_survives_garbage_body():
    res = client.post("/api/v1/shop/payments/webhook",
                      content=b"esto no es json",
                      headers={"Content-Type": "application/json"})
    assert res.status_code == 200
