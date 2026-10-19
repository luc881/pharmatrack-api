"""Destino del animal (purpose): venta, pie de cría y crianza."""
from fastapi import status

from .test_animals import (
    _make_taxonomy, _create_animal, animals_get, animals_post, animals_put,
    species_post, morphs_post,
)


def _package_species(auth_headers):
    _, _, genus, _, _ = _make_taxonomy(auth_headers)
    sp = species_post(
        json={"genus_id": genus["id"], "name": "Paquetera", "sale_format": "package",
              "package_size": 6},
        headers=auth_headers,
    ).json()
    return sp


def _morph(auth_headers, sp, name):
    return morphs_post(json={"species_id": sp["id"], "name": name}, headers=auth_headers).json()


def test_create_defaults_to_sale_and_accepts_breeder(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    assert _create_animal(auth_headers, sp["id"])["purpose"] == "sale"
    assert _create_animal(auth_headers, sp["id"], purpose="breeder")["purpose"] == "breeder"


def test_list_filters_by_purpose(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"])
    _create_animal(auth_headers, sp["id"], purpose="growing")
    data = animals_get(params={"purpose": "growing"}, headers=auth_headers).json()
    assert data["total"] == 1


def test_update_rejects_purpose_field(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"])
    r = animals_put(str(a["id"]), json={"purpose": "breeder"}, headers=auth_headers)
    assert r.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reserve_only_for_sale(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"], purpose="breeder")
    r = animals_put(str(a["id"]), json={"status": "reserved"}, headers=auth_headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "venta" in r.json()["detail"]


def test_non_sale_colony_to_zero_stays_available(auth_headers):
    sp = _package_species(auth_headers)
    a = _create_animal(auth_headers, sp["id"], purpose="growing", stock=10)
    r = animals_put(str(a["id"]), json={"stock": 0}, headers=auth_headers).json()
    assert r["status"] == "available" and r["stock"] == 0


def test_sale_colony_to_zero_is_sold(auth_headers):
    sp = _package_species(auth_headers)
    a = _create_animal(auth_headers, sp["id"], purpose="sale", stock=10)
    r = animals_put(str(a["id"]), json={"stock": 0}, headers=auth_headers).json()
    assert r["status"] == "sold"


def test_duplicate_bulk_record_rejected(auth_headers):
    sp = _package_species(auth_headers)
    m = _morph(auth_headers, sp, "Orange")
    _create_animal(auth_headers, sp["id"], [m["id"]], purpose="growing", stock=5)
    r = animals_post(json={"species_id": sp["id"], "price": 0, "morph_ids": [m["id"]],
                           "purpose": "growing", "stock": 3}, headers=auth_headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    _create_animal(auth_headers, sp["id"], [m["id"]], purpose="sale", stock=3)


def test_editing_morphs_into_collision_rejected(auth_headers):
    sp = _package_species(auth_headers)
    m = _morph(auth_headers, sp, "Orange")
    _create_animal(auth_headers, sp["id"], [], purpose="growing", stock=5)
    b = _create_animal(auth_headers, sp["id"], [m["id"]], purpose="growing", stock=5)
    r = animals_put(str(b["id"]), json={"morph_ids": []}, headers=auth_headers)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
