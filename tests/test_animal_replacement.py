"""Baja de un ejemplar comprometido: regresa a su estado al borrarla y se
puede cambiar por otro disponible (reserva, venta y entregas pendientes)."""
from .utils import client
from .test_animals import (
    _make_taxonomy, _create_animal, _draft_sale_for_animal, animals_get, animals_put,
)

LOGS = "/api/v1/husbandry-logs"


def _status(auth_headers, animal):
    return animals_get(str(animal["id"]), headers=auth_headers).json()


def _death(auth_headers, sp, animal, **extra):
    return client.post(LOGS, json={"species_id": sp["id"], "log_date": "2026-10-12",
                                   "animal_id": animal["id"], "deaths": 1, **extra}, headers=auth_headers)


def test_reserved_death_restores_reserved_and_swap_moves_reservation(auth_headers, db_session):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    dead = _create_animal(auth_headers, sp["id"], code="RAU-001")
    repl = _create_animal(auth_headers, sp["id"], code="RAU-003")
    animals_put(str(dead["id"]), json={"status": "reserved"}, headers=auth_headers)

    # sin cambio: borrar la baja lo deja reservado otra vez
    log = _death(auth_headers, sp, dead)
    assert log.status_code == 201, log.text
    assert log.json()["prev_status"] == "reserved"
    assert client.delete(f"{LOGS}/{log.json()['id']}", headers=auth_headers).status_code == 204
    assert _status(auth_headers, dead)["status"] == "reserved"

    # con cambio: la reserva pasa a RAU-003; deshacer la regresa
    log = _death(auth_headers, sp, dead, replacement_animal_id=repl["id"])
    assert log.status_code == 201, log.text
    assert log.json()["replacement_code"] == "RAU-003"
    assert _status(auth_headers, dead)["status"] == "deceased"
    assert _status(auth_headers, repl)["status"] == "reserved"

    # la baja con cambio no se edita, pero sus notas sí
    put = client.put(f"{LOGS}/{log.json()['id']}", json={"species_id": sp["id"], "log_date": "2026-10-12",
                     "animal_id": dead["id"], "deaths": 1, "replacement_animal_id": repl["id"],
                     "notes": "Se le avisó al cliente"}, headers=auth_headers)
    assert put.status_code == 200, put.text
    assert client.put(f"{LOGS}/{log.json()['id']}", json={"species_id": sp["id"], "log_date": "2026-10-12",
                      "animal_id": dead["id"], "deaths": 1}, headers=auth_headers).status_code == 400

    assert client.delete(f"{LOGS}/{log.json()['id']}", headers=auth_headers).status_code == 204
    assert _status(auth_headers, dead)["status"] == "reserved"
    assert _status(auth_headers, repl)["status"] == "available"


def test_sold_death_swaps_sale_and_undo(auth_headers, db_session,
                                        test_user_with_role_permissions_branch_auth, test_branch):
    from pharmatrack.models.sale_details.orm import SaleDetail
    from pharmatrack.models.sales.orm import Sale

    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    dead = _create_animal(auth_headers, sp["id"], code="RAU-001")
    repl = _create_animal(auth_headers, sp["id"], code="RAU-003")
    sale, detail = _draft_sale_for_animal(db_session, test_user_with_role_permissions_branch_auth, test_branch, dead)
    assert client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers).status_code == 200

    # el formulario sabe a qué venta iba
    info = client.get(f"/api/v1/animals/{dead['id']}/commitments", headers=auth_headers).json()
    assert info["status"] == "sold" and info["sale"]["id"] == sale.id

    # vendido sin entregar: antes no se podía anotar la baja (sin stock)
    log = _death(auth_headers, sp, dead, replacement_animal_id=repl["id"])
    assert log.status_code == 201, log.text
    assert _status(auth_headers, dead)["status"] == "deceased"
    r = _status(auth_headers, repl)
    assert r["status"] == "sold" and r["stock"] == 0

    db_session.expire_all()
    assert db_session.get(SaleDetail, detail.id).product_id == repl["product_id"]
    assert "RAU-001 → RAU-003" in db_session.get(Sale, sale.id).description

    # deshacer: la venta regresa a RAU-001 y RAU-003 vuelve al inventario
    assert client.delete(f"{LOGS}/{log.json()['id']}", headers=auth_headers).status_code == 204
    assert _status(auth_headers, dead)["status"] == "sold"
    r = _status(auth_headers, repl)
    assert r["status"] == "available" and r["stock"] == 1
    db_session.expire_all()
    assert db_session.get(SaleDetail, detail.id).product_id == dead["product_id"]


def test_sold_death_without_swap_blocks_reintegrating_refund(
    auth_headers, db_session, test_user_with_role_permissions_branch_auth, test_branch
):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    dead = _create_animal(auth_headers, sp["id"])
    sale, detail = _draft_sale_for_animal(db_session, test_user_with_role_permissions_branch_auth, test_branch, dead)
    client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)

    assert _death(auth_headers, sp, dead).status_code == 201
    assert _status(auth_headers, dead)["status"] == "deceased"

    refund = {"product_id": dead["product_id"], "quantity": 1, "sale_detail_id": detail.id,
              "user_id": test_user_with_role_permissions_branch_auth.id}
    res = client.post("/api/v1/refundproducts", json={**refund, "is_reintegrable": True}, headers=auth_headers)
    assert res.status_code == 400 and "murió" in res.json()["detail"]
    res = client.post("/api/v1/refundproducts", json={**refund, "is_reintegrable": False}, headers=auth_headers)
    assert res.status_code == 201, res.text
    assert _status(auth_headers, dead)["status"] == "deceased"


def test_pending_delivery_follows_the_swap(auth_headers, db_session):
    from pharmatrack.models.deliveries.orm import Delivery

    def get_delivery(delivery_id):
        db_session.expire_all()
        return db_session.get(Delivery, delivery_id)

    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    dead = _create_animal(auth_headers, sp["id"], code="RAU-001")
    repl = _create_animal(auth_headers, sp["id"], code="RAU-003")
    sold_out = _create_animal(auth_headers, sp["id"], code="RAU-004")
    animals_put(str(sold_out["id"]), json={"status": "reserved"}, headers=auth_headers)
    delivery = client.post("/api/v1/deliveries", json={
        "buyer_name": "Ana", "scheduled_date": "2026-10-20",
        "items_given": [{"description": "Gárgola RAU-001", "animal_id": dead["id"]}],
    }, headers=auth_headers).json()

    # el reemplazo debe estar disponible y ser de la especie
    assert _death(auth_headers, sp, dead, replacement_animal_id=sold_out["id"]).status_code == 400
    log = _death(auth_headers, sp, dead, replacement_animal_id=repl["id"])
    assert log.status_code == 201, log.text

    d = get_delivery(delivery["id"])
    assert d.items_given[0] == {"description": "Gárgola RAU-003", "quantity": 1, "animal_id": repl["id"]}
    assert "RAU-001 → RAU-003" in d.notes

    client.delete(f"{LOGS}/{log.json()['id']}", headers=auth_headers)
    assert get_delivery(delivery["id"]).items_given[0]["animal_id"] == dead["id"]


def test_swap_needs_a_commitment(auth_headers, db_session):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    dead = _create_animal(auth_headers, sp["id"])
    repl = _create_animal(auth_headers, sp["id"])
    res = _death(auth_headers, sp, dead, replacement_animal_id=repl["id"])
    assert res.status_code == 400 and "nada que cambiar" in res.json()["detail"]
    assert _status(auth_headers, dead)["status"] == "available"
