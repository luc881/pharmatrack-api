"""Mover entre venta, pie de cría y crianza (POST /animals/{id}/move)."""
from datetime import date

from fastapi import HTTPException, status

from .utils import client
from .test_animals import (
    _make_taxonomy, _create_animal, animals_get, animals_put, species_post, morphs_post,
)


def _move(auth_headers, animal_id, **body):
    return client.post(f"/api/v1/animals/{animal_id}/move", json=body, headers=auth_headers)


def _bulk_species(auth_headers, sale_format="colony", package_size=None):
    _, _, genus, _, _ = _make_taxonomy(auth_headers)
    payload = {"genus_id": genus["id"], "name": "Cultivo", "sale_format": sale_format}
    if package_size:
        payload["package_size"] = package_size
    return species_post(json=payload, headers=auth_headers).json()


def _get(auth_headers, animal_id):
    return animals_get(str(animal_id), headers=auth_headers).json()


def _count(auth_headers, species_id):
    return animals_get(params={"species_id": species_id}, headers=auth_headers).json()["total"]


def test_move_individual_flips_purpose(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"])
    r = _move(auth_headers, a["id"], purpose="breeder")
    assert r.status_code == 200, r.text
    assert [x["id"] for x in r.json()] == [a["id"]]
    got = _get(auth_headers, a["id"])
    assert got["purpose"] == "breeder"
    assert got["product_id"] == a["product_id"]
    assert client.get(f"/api/v1/products/{a['product_id']}", headers=auth_headers).status_code == 200


def test_move_reserved_rejected(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"])
    animals_put(str(a["id"]), json={"status": "reserved"}, headers=auth_headers)
    r = _move(auth_headers, a["id"], purpose="breeder")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "activo" in r.json()["detail"]
    assert _get(auth_headers, a["id"])["purpose"] == "sale"


def test_move_to_sale_requires_price(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"], purpose="growing", price=0)
    r = _move(auth_headers, a["id"], purpose="sale")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json()["detail"] == "Ponle precio para ponerlo en venta."
    assert _get(auth_headers, a["id"])["purpose"] == "growing"

    r = _move(auth_headers, a["id"], purpose="sale", price=350)
    assert r.status_code == 200, r.text
    assert r.json()[0]["purpose"] == "sale" and r.json()[0]["price"] == 350
    product = client.get(f"/api/v1/products/{a['product_id']}", headers=auth_headers).json()
    assert float(product["price_retail"]) == 350


def test_bulk_partial_creates_sibling(auth_headers):
    sp = _bulk_species(auth_headers)
    m = morphs_post(json={"species_id": sp["id"], "name": "Orange"}, headers=auth_headers).json()
    src = _create_animal(auth_headers, sp["id"], [m["id"]], purpose="growing", stock=10, price=0)
    r = _move(auth_headers, src["id"], purpose="sale", quantity=4, price=200)
    assert r.status_code == 200, r.text
    out, new = r.json()
    assert out["id"] == src["id"] and out["stock"] == 6 and out["purpose"] == "growing"
    assert new["id"] != src["id"] and new["stock"] == 4 and new["purpose"] == "sale"
    assert new["price"] == 200 and new["sex"] == "unknown"
    assert [x["id"] for x in new["morphs"]] == [m["id"]]
    assert new["price_cost"] == src["price_cost"]


def test_bulk_partial_into_existing_sibling(auth_headers):
    sp = _bulk_species(auth_headers)
    src = _create_animal(auth_headers, sp["id"], purpose="growing", stock=10)
    sib = _create_animal(auth_headers, sp["id"], purpose="sale", stock=2)
    r = _move(auth_headers, src["id"], purpose="sale", quantity=3)
    assert r.status_code == 200, r.text
    out, target = r.json()
    assert out["stock"] == 7
    assert target["id"] == sib["id"] and target["stock"] == 5
    assert _count(auth_headers, sp["id"]) == 2


def test_bulk_all_without_sibling_flips(auth_headers, db_session):
    from pharmatrack.models.husbandry_logs.orm import HusbandryLog

    sp = _bulk_species(auth_headers)
    src = _create_animal(auth_headers, sp["id"], purpose="growing", stock=10)
    db_session.add(HusbandryLog(species_id=sp["id"], animal_id=src["id"],
                                log_date=date(2026, 10, 19), fed=True))
    db_session.commit()

    r = _move(auth_headers, src["id"], purpose="breeder")
    assert r.status_code == 200, r.text
    assert [x["id"] for x in r.json()] == [src["id"]]
    got = _get(auth_headers, src["id"])
    assert got["purpose"] == "breeder" and got["stock"] == 10
    log = db_session.query(HusbandryLog).one()
    assert log.animal_id == src["id"]
    assert _count(auth_headers, sp["id"]) == 1


def test_bulk_all_into_sibling_leaves_source_empty(auth_headers):
    sp = _bulk_species(auth_headers)
    src = _create_animal(auth_headers, sp["id"], purpose="sale", stock=4)
    sib = _create_animal(auth_headers, sp["id"], purpose="growing", stock=1)
    r = _move(auth_headers, src["id"], purpose="growing")
    assert r.status_code == 200, r.text
    out, target = r.json()
    # vaciado por mover, aunque esté en venta, no queda vendido
    assert out["stock"] == 0 and out["status"] == "available" and out["purpose"] == "sale"
    assert target["id"] == sib["id"] and target["stock"] == 5


def test_package_growing_to_sale_converts(auth_headers):
    sp = _bulk_species(auth_headers, "package", 6)
    src = _create_animal(auth_headers, sp["id"], purpose="growing", stock=40)
    r = _move(auth_headers, src["id"], purpose="sale", quantity=3)
    assert r.status_code == 200, r.text
    out, new = r.json()
    assert out["stock"] == 22 and out["purpose"] == "growing"
    assert new["stock"] == 3 and new["purpose"] == "sale"


def test_package_sale_to_growing_converts(auth_headers):
    sp = _bulk_species(auth_headers, "package", 6)
    src = _create_animal(auth_headers, sp["id"], purpose="sale", stock=5)
    sib = _create_animal(auth_headers, sp["id"], purpose="growing", stock=4)
    r = _move(auth_headers, src["id"], purpose="growing", quantity=2)
    assert r.status_code == 200, r.text
    out, target = r.json()
    assert out["stock"] == 3
    assert target["id"] == sib["id"] and target["stock"] == 16


def test_package_not_enough_rejected(auth_headers):
    sp = _bulk_species(auth_headers, "package", 6)
    src = _create_animal(auth_headers, sp["id"], purpose="growing", stock=17)
    r = _move(auth_headers, src["id"], purpose="sale", quantity=3)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json()["detail"] == "No alcanzan: hay 17."
    assert _get(auth_headers, src["id"])["stock"] == 17
    assert _count(auth_headers, sp["id"]) == 1


def test_failed_move_changes_nothing(auth_headers, monkeypatch):
    from pharmatrack.utils import animal_records

    real_new_animal = animal_records.new_animal

    def flush_then_fail(*args, **kwargs):
        # el registro nuevo llega a la base (flush) antes de fallar
        real_new_animal(*args, **kwargs)
        raise HTTPException(status_code=400, detail="boom")

    monkeypatch.setattr(animal_records, "new_animal", flush_then_fail)
    sp = _bulk_species(auth_headers)
    src = _create_animal(auth_headers, sp["id"], purpose="growing", stock=10)
    r = _move(auth_headers, src["id"], purpose="sale", quantity=4, price=200)
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json()["detail"] == "boom"
    assert _get(auth_headers, src["id"])["stock"] == 10
    assert _count(auth_headers, sp["id"]) == 1
