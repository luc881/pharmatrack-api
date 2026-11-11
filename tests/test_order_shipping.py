"""Guías de envío de un pedido (Envia.com), con sus respuestas simuladas."""
import pytest
from fastapi import HTTPException

from pharmatrack.config import settings
from pharmatrack.utils import envia

from .test_animals import _create_animal, _make_taxonomy
from .test_shop import _sign_in, fake_google  # noqa: F401
from .utils import client

BODY = {
    "destination": {
        "name": "Cliente Prueba", "phone": "5512345678", "street": "Insurgentes Sur",
        "number": "3000", "district": "Coyoacán", "city": "Ciudad de México",
        "state": "Ciudad de México", "postal_code": "04530",
    },
    "package": {"content": "Insumos de terrario", "weight": 1.5,
                "length": 30, "width": 20, "height": 15, "declared_value": 500},
}


@pytest.fixture
def fake_envia(monkeypatch):
    """Envia.com simulado: lista de estados y paqueterías, cotización y guía."""
    monkeypatch.setattr(settings, "envia_api_token", "token-de-prueba")
    monkeypatch.setattr(settings, "envia_origin", (
        '{"name":"Tienda","phone":"5500000000","street":"Calle 1","city":"CDMX",'
        '"state":"CX","postalCode":"07000"}'))
    envia._state_codes.cache_clear()
    envia.carriers.cache_clear()
    sent = []

    def _call(method, url, **kwargs):
        if url.endswith("/state"):
            return {"data": [{"name": "Ciudad de México", "code_2_digits": "CX"}]}
        if url.endswith("/carrier"):
            return {"data": [{"name": "dhl", "active": True}, {"name": "fedex", "active": True},
                             {"name": "caido", "active": True}]}
        body = kwargs["json"]
        sent.append((url, body))
        carrier = body["shipment"]["carrier"]
        if url.endswith("/ship/rate/"):
            if carrier == "caido":
                raise HTTPException(status_code=502, detail="sin servicio")
            price = {"dhl": "185.20", "fedex": "120.00"}[carrier]
            return {"data": [{"carrier": carrier, "service": "ground",
                              "serviceDescription": "Terrestre", "deliveryEstimate": "2-4 días",
                              "totalPrice": price, "currency": "MXN"}]}
        return {"data": [{"carrier": carrier, "service": body["shipment"]["service"],
                          "trackingNumber": "7520610403",
                          "trackUrl": "https://tracking.envia.com/7520610403",
                          "label": "https://files.envia.com/labels/7520610403.pdf",
                          "totalPrice": 120.0, "currency": "MXN"}]}

    monkeypatch.setattr(envia, "_call", _call)
    yield sent
    envia._state_codes.cache_clear()
    envia.carriers.cache_clear()


@pytest.fixture
def order(fake_google, auth_headers):  # noqa: F811
    _group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], price=500.0)
    res = client.post("/api/v1/shop/orders", headers=_sign_in(),
                      json={"items": [{"key": f"s{sp['id']}-u", "qty": 1}]})
    assert res.status_code == 201, res.text
    return res.json()


def test_cotiza_de_la_mas_barata_a_la_mas_cara(order, auth_headers, fake_envia):
    res = client.post(f"/api/v1/orders/{order['id']}/shipping/rates", headers=auth_headers, json=BODY)
    assert res.status_code == 200, res.text
    rates = res.json()["rates"]
    # la paquetería que falló no aparece y no tumba la cotización
    assert [(r["carrier"], r["price"]) for r in rates] == [("fedex", 120.0), ("dhl", 185.2)]
    # el estado viaja con el código de Envia, no con el nombre
    assert fake_envia[0][1]["destination"]["state"] == "CX"


def test_genera_la_guia_una_sola_vez(order, auth_headers, fake_envia):
    url = f"/api/v1/orders/{order['id']}/shipping/label"
    body = {**BODY, "carrier": "fedex", "service": "ground"}
    res = client.post(url, headers=auth_headers, json=body)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["tracking_number"] == "7520610403"
    assert data["label_url"].endswith(".pdf")
    assert data["shipping_cost"] == 120.0

    # segundo clic: no se compra otra guía
    again = client.post(url, headers=auth_headers, json=body)
    assert again.status_code == 409
    assert sum(1 for sent_url, _ in fake_envia if sent_url.endswith("/ship/generate/")) == 1


def test_sin_configurar_responde_503(order, auth_headers):
    res = client.post(f"/api/v1/orders/{order['id']}/shipping/rates", headers=auth_headers, json=BODY)
    assert res.status_code == 503


def test_estado_desconocido(order, auth_headers, fake_envia):
    body = {**BODY, "destination": {**BODY["destination"], "state": "Narnia"}}
    res = client.post(f"/api/v1/orders/{order['id']}/shipping/rates", headers=auth_headers, json=body)
    assert res.status_code == 422


# ── Envíos sueltos (sin pedido del sitio) ────────────────────────────────────

def test_envio_suelto_cotiza_y_genera_sin_pedido(auth_headers, fake_envia):
    rates = client.post("/api/v1/shipments/rates", headers=auth_headers, json=BODY)
    assert rates.status_code == 200, rates.text
    assert rates.json()["rates"][0]["carrier"] == "fedex"

    body = {**BODY, "carrier": "fedex", "service": "ground",
            "idempotency_key": "clave-de-prueba-1", "note": "WhatsApp: Juan"}
    res = client.post("/api/v1/shipments", headers=auth_headers, json=body)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["tracking_number"] == "7520610403"
    assert data["cost"] == 120.0
    assert "04530" in data["address"]

    # segundo clic con la misma clave: devuelve el mismo envío y no compra otra guía
    again = client.post("/api/v1/shipments", headers=auth_headers, json=body)
    assert again.status_code == 200 and again.json()["id"] == data["id"]
    assert sum(1 for url, _ in fake_envia if url.endswith("/ship/generate/")) == 1

    listed = client.get("/api/v1/shipments", headers=auth_headers).json()
    assert [s["note"] for s in listed["data"]] == ["WhatsApp: Juan"]


def test_envio_suelto_que_envia_rechaza_no_deja_registro(auth_headers, fake_envia, monkeypatch):
    def boom(*args, **kwargs):
        raise HTTPException(status_code=502, detail="Envia.com rechazó la solicitud")
    monkeypatch.setattr(envia, "generate", boom)
    body = {**BODY, "carrier": "fedex", "service": "ground", "idempotency_key": "clave-de-prueba-2"}
    assert client.post("/api/v1/shipments", headers=auth_headers, json=body).status_code == 502
    assert client.get("/api/v1/shipments", headers=auth_headers).json()["data"] == []


def test_guia_rechazada_con_200_muestra_el_motivo(auth_headers, fake_envia, monkeypatch):
    real = envia._call

    def _call(method, url, **kwargs):
        if url.endswith("/ship/generate/"):
            return {"meta": "error", "error": {"code": 1125, "message": "Saldo insuficiente"}}
        return real(method, url, **kwargs)

    monkeypatch.setattr(envia, "_call", _call)
    body = {**BODY, "carrier": "fedex", "service": "ground", "idempotency_key": "clave-de-prueba-3"}
    res = client.post("/api/v1/shipments", headers=auth_headers, json=body)
    assert res.status_code == 502
    assert "Saldo insuficiente" in res.json()["detail"]
