"""Control de entregas: ventas y cambios en persona (solo registro)."""
from .utils import client
from .test_animals import _make_taxonomy, _create_animal, animals_get

URL = "/api/v1/deliveries"


def _payload(**over):
    body = {
        "buyer_name": "Ana",
        "buyer_contact": "5512345678",
        "scheduled_date": "2026-10-11",
        "scheduled_time": "17:30",
        "place": "Metro Tlatelolco",
        "items_given": [{"description": "Isópodos Cubaris x6"}],
        "amount": 350,
        "payment_method": "cash",
    }
    body.update(over)
    return body


def test_delivery_crud_status_and_order(auth_headers, db_session):
    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    a = client.post(URL, json=_payload(), headers=auth_headers)
    assert a.status_code == 201, a.text
    body = a.json()
    assert body["status"] == "pending" and body["delivered_at"] is None
    assert body["items_given"] == [{"description": "Isópodos Cubaris x6", "quantity": 1, "animal_id": None}]
    assert body["user_name"]

    trade = client.post(URL, json=_payload(
        kind="trade", buyer_name="Beto", scheduled_date="2026-10-11", scheduled_time="12:00",
        items_given=[{"description": "Hamorii", "animal_id": animal["id"]}],
        items_received=[{"description": "Dubia adultas", "quantity": 20}], amount=None,
    ), headers=auth_headers)
    assert trade.status_code == 201, trade.text
    later = client.post(URL, json=_payload(buyer_name="Caro", scheduled_date="2026-10-12", scheduled_time=None),
                        headers=auth_headers).json()

    # pendientes: la más próxima primero (mismo día por hora)
    names = [d["buyer_name"] for d in client.get(URL, params={"status": "pending"}, headers=auth_headers).json()["data"]]
    assert names == ["Beto", "Ana", "Caro"]
    assert [d["buyer_name"] for d in client.get(URL, params={"q": "tlatelolco", "date_from": "2026-10-12"},
                                               headers=auth_headers).json()["data"]] == ["Caro"]

    # marcar entregada pone delivered_at; regresar a pendiente lo quita
    done = client.put(f"{URL}/{body['id']}/status", json={"status": "delivered"}, headers=auth_headers).json()
    assert done["status"] == "delivered" and done["delivered_at"]
    # editar una ya entregada conserva su delivered_at
    edited = client.put(f"{URL}/{body['id']}", json=_payload(status="delivered", paid=True), headers=auth_headers).json()
    assert edited["delivered_at"] == done["delivered_at"] and edited["paid"] is True
    back = client.put(f"{URL}/{body['id']}/status", json={"status": "pending"}, headers=auth_headers).json()
    assert back["delivered_at"] is None

    # solo registro: el inventario del animal no cambia
    assert animals_get(path=f"/{animal['id']}", headers=auth_headers).json()["stock"] == 1

    assert client.delete(f"{URL}/{later['id']}", headers=auth_headers).status_code == 204
    assert client.put(f"{URL}/{later['id']}/status", json={"status": "delivered"}, headers=auth_headers).status_code == 404


def test_delivery_validation(auth_headers, db_session):
    bad = [
        _payload(buyer_name=""),
        _payload(scheduled_time="25:00"),
        _payload(kind="gift"),
        _payload(payment_method="crypto"),
        _payload(amount=-1),
        _payload(items_given=[{"description": ""}]),
        _payload(extra="x"),
        _payload(sale_id=999999),
        _payload(order_id=999999),
        _payload(items_given=[{"description": "x", "animal_id": 999999}]),
    ]
    for body in bad:
        assert client.post(URL, json=body, headers=auth_headers).status_code in (400, 422), body
    assert client.get(URL).status_code == 401


def test_delivery_summary(auth_headers, db_session):
    rows = [
        _payload(scheduled_date="2026-10-01", amount=300, paid=True, payment_method="transfer"),
        _payload(scheduled_date="2026-10-05", amount=200, paid=True, payment_method="cash", status="delivered"),
        _payload(scheduled_date="2026-10-06", amount=50, paid=True, payment_method=None),
        _payload(scheduled_date="2026-09-30", amount=999, paid=True, payment_method="cash"),  # fuera de rango
        _payload(scheduled_date="2026-10-07", amount=120, paid=False),  # por cobrar
        _payload(scheduled_date="2026-10-08", amount=500, paid=True, status="cancelled"),  # cancelada: no cuenta
        _payload(scheduled_date="2026-11-20", amount=80, paid=False),  # por cobrar aunque sea de otro mes
    ]
    for body in rows:
        assert client.post(URL, json=body, headers=auth_headers).status_code == 201

    s = client.get(f"{URL}/summary", params={"date_from": "2026-10-01", "date_to": "2026-10-31"},
                   headers=auth_headers).json()
    assert float(s["collected"]) == 550
    assert float(s["transfer"]) == 300 and float(s["cash"]) == 200 and float(s["other"]) == 50
    assert float(s["to_collect"]) == 200 and s["to_collect_count"] == 2
    assert s["pending_count"] == 5
