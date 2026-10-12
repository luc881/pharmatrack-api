"""«Murió»: lo pone una baja en la bitácora y no choca con ventas, edición,
borrado ni el sitio público."""
from fastapi import status

from .utils import client
from .test_animals import (
    _make_taxonomy, _create_animal, _draft_sale_for_animal, animals_get, animals_put, animals_delete,
)

LOGS = "/api/v1/husbandry-logs"


def test_death_marks_deceased_and_blocks_everything(
    auth_headers, db_session, test_user_with_role_permissions_branch_auth, test_branch
):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    get = lambda: animals_get(str(animal["id"]), headers=auth_headers).json()  # noqa: E731

    # un borrador en el POS antes de que muera
    sale, _ = _draft_sale_for_animal(db_session, test_user_with_role_permissions_branch_auth, test_branch, animal)

    log = client.post(LOGS, json={"species_id": sp["id"], "log_date": "2026-10-10",
                                  "animal_id": animal["id"], "deaths": 1}, headers=auth_headers)
    assert log.status_code == 201, log.text
    assert get()["status"] == "deceased" and get()["stock"] == 0

    # no se vende (mensaje claro), no se revive editando, no se borra
    res = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert res.status_code == 400 and animal["code"] in res.json()["detail"]
    assert animals_put(str(animal["id"]), json={"status": "available"}, headers=auth_headers).status_code == 400
    assert animals_put(str(animal["id"]), json={"price": 999}, headers=auth_headers).status_code == 200
    assert get()["status"] == "deceased"
    assert animals_delete(str(animal["id"]), headers=auth_headers).status_code == 400

    # el sitio no lo muestra ni con link directo
    assert client.get(f"/api/v1/public/animals/{animal['id']}").status_code == 404
    rows = client.get("/api/v1/public/animals", params={"include_unavailable": True}).json()["data"]
    assert all(r["id"] != animal["id"] for r in rows)

    # nadie lo pone a mano
    other = _create_animal(auth_headers, sp["id"])
    assert animals_put(str(other["id"]), json={"status": "deceased"}, headers=auth_headers).status_code == 422

    # borrar la baja lo regresa y ya se puede vender
    assert client.delete(f"{LOGS}/{log.json()['id']}", headers=auth_headers).status_code == 204
    assert get()["status"] == "available" and get()["stock"] == 1
    assert client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers).status_code == 200
    assert get()["status"] == "sold"


def test_colony_partial_deaths_stay_available_and_restock_revives(auth_headers, db_session):
    from .test_animal_stock import _make_colony_species

    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    colony = _make_colony_species(auth_headers, sp)
    cepa = _create_animal(auth_headers, colony["id"], stock=5)
    get = lambda: animals_get(str(cepa["id"]), headers=auth_headers).json()  # noqa: E731
    base = {"species_id": colony["id"], "log_date": "2026-10-10", "animal_id": cepa["id"]}

    client.post(LOGS, json={**base, "deaths": 2}, headers=auth_headers)
    assert get()["status"] == "available" and get()["stock"] == 3
    client.post(LOGS, json={**base, "deaths": 3}, headers=auth_headers)
    assert get()["status"] == "deceased"

    # poner stock 0 a mano no lo vuelve «vendido»; resurtir lo reactiva
    animals_put(str(cepa["id"]), json={"stock": 0}, headers=auth_headers)
    assert get()["status"] == "deceased"
    assert animals_put(str(cepa["id"]), json={"stock": 4}, headers=auth_headers).status_code == 200
    assert get()["status"] == "available"
