"""Bitácora del plan de manejo de especies."""
from .utils import client
from .test_animals import _make_taxonomy

URL = "/api/v1/husbandry-logs"


def test_log_roundtrip_filters_and_implied_fed(auth_headers, db_session):
    _root, _sub, _genus, sp, morph = _make_taxonomy(auth_headers)

    # palomita sola
    quick = client.post(URL, json={"species_id": sp["id"], "log_date": "2026-10-09", "fed": True}, headers=auth_headers)
    assert quick.status_code == 201, quick.text
    assert quick.json()["fed"] is True
    assert quick.json()["user_name"]

    # detalle: con gramos, `fed` queda en True aunque no se mande
    full = client.post(URL, json={
        "species_id": sp["id"], "morph_id": morph["id"], "log_date": "2026-10-10",
        "food_type": "Papilla", "grams": 3.5, "appetite": "good",
        "activities": ["misted", "molt", "misted"], "notes": "Todo bien",
    }, headers=auth_headers)
    assert full.status_code == 201, full.text
    body = full.json()
    assert body["fed"] is True
    assert body["activities"] == ["misted", "molt"]
    assert body["morph_name"] == morph["name"]
    assert "Hamorii" in body["species_name"]

    # rechazó la comida: no se marca como comido
    refused = client.post(URL, json={
        "species_id": sp["id"], "log_date": "2026-10-10", "food_type": "Grillos", "pieces": 4, "appetite": "refused",
    }, headers=auth_headers).json()
    assert refused["fed"] is False

    rows = client.get(URL, params={"species_id": sp["id"]}, headers=auth_headers).json()["data"]
    assert [r["log_date"] for r in rows] == ["2026-10-10", "2026-10-10", "2026-10-09"]
    rows = client.get(URL, params={"date_from": "2026-10-10", "morph_id": morph["id"]}, headers=auth_headers).json()["data"]
    assert [r["id"] for r in rows] == [body["id"]]

    upd = client.put(f"{URL}/{quick.json()['id']}", json={
        "species_id": sp["id"], "log_date": "2026-10-09", "fed": False, "notes": "Corrección",
    }, headers=auth_headers)
    assert upd.status_code == 200, upd.text
    assert upd.json()["notes"] == "Corrección" and upd.json()["fed"] is False

    assert client.delete(f"{URL}/{quick.json()['id']}", headers=auth_headers).status_code == 204
    assert client.put(f"{URL}/{quick.json()['id']}", json={"species_id": sp["id"], "log_date": "2026-10-09"},
                      headers=auth_headers).status_code == 404


def test_log_validation(auth_headers, db_session):
    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _r2, _s2, _g2, other_sp, other_morph = _make_taxonomy(
        auth_headers, group_name="Insectos", subgroup_name="Fásmidos", genus_name="Phyllium",
        species_name="gardabagusi", morph_name="Argopuro",
    )
    bad = [
        {"species_id": sp["id"], "log_date": "2026-10-10", "morph_id": other_morph["id"]},  # morph ajeno
        {"species_id": sp["id"], "log_date": "2026-10-10", "pieces": -1},
        {"species_id": sp["id"], "log_date": "2026-10-10", "appetite": "meh"},
        {"species_id": sp["id"], "log_date": "2026-10-10", "activities": ["dance"]},
        {"species_id": sp["id"]},  # sin fecha
    ]
    for payload in bad:
        assert client.post(URL, json=payload, headers=auth_headers).status_code in (400, 422), payload
    assert client.post(URL, json={"species_id": 999999, "log_date": "2026-10-10"}, headers=auth_headers).status_code == 404
    assert client.get(URL).status_code == 401


def test_deaths_deduct_and_restore_stock(auth_headers, db_session):
    from .test_animal_stock import _make_colony_species
    from .test_animals import _create_animal, animals_get

    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    colony = _make_colony_species(auth_headers, sp)
    cepa = _create_animal(auth_headers, colony["id"], stock=10)
    stock = lambda: animals_get(path=f"/{cepa['id']}", headers=auth_headers).json()  # noqa: E731

    base = {"species_id": colony["id"], "log_date": "2026-10-10", "animal_id": cepa["id"]}
    log = client.post(URL, json={**base, "deaths": 3}, headers=auth_headers)
    assert log.status_code == 201, log.text
    assert log.json()["stock_deducted"] == 3
    assert "deaths" in log.json()["activities"]
    assert stock()["stock"] == 7

    # más bajas que inventario: rechazado y sin tocar nada
    assert client.post(URL, json={**base, "deaths": 8}, headers=auth_headers).status_code == 400
    assert stock()["stock"] == 7

    # editar: regresa las 3 y descuenta 7 → murió (no «vendido»)
    upd = client.put(f"{URL}/{log.json()['id']}", json={**base, "deaths": 10}, headers=auth_headers)
    assert upd.status_code == 200, upd.text
    assert stock()["stock"] == 0 and stock()["status"] == "deceased"

    # borrar: regresa todo y vuelve a la venta
    assert client.delete(f"{URL}/{log.json()['id']}", headers=auth_headers).status_code == 204
    assert stock()["stock"] == 10 and stock()["status"] == "available"

    # el ejemplar debe ser de la especie
    other = _create_animal(auth_headers, sp["id"])
    assert client.post(URL, json={**base, "animal_id": other["id"], "deaths": 1},
                       headers=auth_headers).status_code == 400


def test_plan_status(auth_headers, db_session):
    from datetime import timedelta
    from pharmatrack.api.routes.husbandry_logs import today_mx

    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    plan = [
        {"kind": "food", "name": "Papilla", "every_days": 3},
        {"kind": "food", "name": "Grillos", "every_days": 7},
        {"kind": "supplement", "name": "Calcio con D3", "every_days": 14},
    ]
    res = client.put(f"/api/v1/species/{sp['id']}", json={"husbandry_plan": plan}, headers=auth_headers)
    assert res.status_code == 200, res.text
    assert res.json()["husbandry_plan"] == plan
    # privado: no sale en el público
    assert all("husbandry_plan" not in a["species"] for a in client.get("/api/v1/public/animals").json()["data"])

    today = today_mx()
    day = lambda n: str(today - timedelta(days=n))  # noqa: E731
    for payload in [
        {"log_date": day(5), "food_type": "papilla ", "grams": 2},  # papilla hace 5 → 2 días tarde
        {"log_date": day(2), "food_type": "Grillos", "pieces": 4, "appetite": "refused"},  # no comió: no cuenta
        {"log_date": day(1), "supplement": "Calcio con D3", "activities": ["molt"]},
    ]:
        assert client.post(URL, json={"species_id": sp["id"], **payload}, headers=auth_headers).status_code == 201

    rows = client.get(f"{URL}/status", headers=auth_headers).json()
    row = next(r for r in rows if r["species_id"] == sp["id"])
    by = {p["name"]: p for p in row["plan"]}
    assert by["Papilla"]["last_done"] == day(5) and by["Papilla"]["days_overdue"] == 2
    assert by["Grillos"]["last_done"] is None and by["Grillos"]["days_overdue"] == 0
    assert by["Calcio con D3"]["days_overdue"] == -13
    assert [p["name"] for p in row["plan"]][0] == "Papilla"  # lo más atrasado primero
    assert row["last_fed"] == day(5)
    if today.day >= 6:  # los registros caen en este mes
        assert row["month"]["molt"] == 1 and row["month"]["feedings"] == 1

    assert client.put(f"/api/v1/species/{sp['id']}", json={"husbandry_plan": [{"kind": "x", "name": "a", "every_days": 1}]},
                      headers=auth_headers).status_code == 422


def test_per_animal_and_assisted_feeding(auth_headers, db_session):
    from .test_animals import _create_animal

    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    a1 = _create_animal(auth_headers, sp["id"], code="EJ-001")
    a2 = _create_animal(auth_headers, sp["id"], code="EJ-002")

    # asistida: cuenta como comida; un ejemplar sin bajas no toca inventario
    res = client.post(URL, json={
        "species_id": sp["id"], "log_date": "2026-10-10", "animal_id": a1["id"],
        "assisted": True, "food_type": "Papilla", "grams": 1,
    }, headers=auth_headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["assisted"] is True and body["fed"] is True
    assert body["animal_code"] == "EJ-001" and body["stock_deducted"] == 0
    assert body["species_common_name"] == sp["common_name"]

    client.post(URL, json={"species_id": sp["id"], "log_date": "2026-10-10", "animal_id": a2["id"], "fed": True},
                headers=auth_headers)
    rows = client.get(URL, params={"animal_id": a1["id"]}, headers=auth_headers).json()["data"]
    assert [r["animal_code"] for r in rows] == ["EJ-001"]


def test_condition_and_weight(auth_headers, db_session):
    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    base = {"species_id": sp["id"], "log_date": "2026-10-10"}

    res = client.post(URL, json={**base, "condition": "other", "condition_note": "Ojo hinchado",
                                 "weight_g": 42.5, "appetite": "poor", "pieces": 2}, headers=auth_headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["condition"] == "other" and body["condition_note"] == "Ojo hinchado"
    assert float(body["weight_g"]) == 42.5 and body["fed"] is True

    for bad in ({"condition": "sleepy"}, {"weight_g": 0}, {"weight_g": -3}):
        assert client.post(URL, json={**base, **bad}, headers=auth_headers).status_code == 422, bad
