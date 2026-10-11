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
