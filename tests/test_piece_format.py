"""Formato «Por pieza»: animales iguales que se venden de uno en uno (insecto
hoja, mantis). Un registro con cantidad por variedad y sexo; al pasar una
especie a este formato, lo que ya está en venta se junta."""
from datetime import date

from fastapi import status

from .utils import client
from .test_animals import _make_taxonomy, _create_animal

ANIMALS = "/api/v1/animals"


def _piece_species(auth_headers, **extra):
    *_, sp, morph = _make_taxonomy(auth_headers, genus_name="Phyllium", species_name="Gardabagusi",
                                   morph_name="Argopuro")
    res = client.put(f"/api/v1/species/{sp['id']}", json={"sale_format": "piece", **extra},
                     headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    return sp, morph


def _stock(animal_id, auth_headers):
    return client.get(f"{ANIMALS}/{animal_id}", headers=auth_headers).json()["stock"]


def test_one_lot_per_variety_and_sex(auth_headers):
    sp, morph = _piece_species(auth_headers)

    females = _create_animal(auth_headers, sp["id"], sex="female", stock=4, price=600)
    assert females["stock"] == 4
    # el nombre del lote lleva el sexo: se distingue en la venta rápida y el ticket
    product = client.get(f"/api/v1/products/{females['product_id']}", headers=auth_headers).json()
    assert "Hembra" in product["title"]

    # otra hembra nominal: ya hay lote, se ajusta su cantidad
    res = client.post(ANIMALS, json={"species_id": sp["id"], "sex": "female", "price": 600,
                                     "price_cost": 0, "stock": 1}, headers=auth_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    # machos, sin sexar y otra variedad: cada uno su lote
    _create_animal(auth_headers, sp["id"], sex="male", stock=3, price=450)
    _create_animal(auth_headers, sp["id"], sex="unknown", stock=20, price=350)
    _create_animal(auth_headers, sp["id"], sex="female", stock=2, morph_ids=[morph["id"]])


def test_switching_to_piece_merges_what_is_for_sale(auth_headers, db_session):
    *_, sp, _morph = _make_taxonomy(auth_headers, genus_name="Extatosoma", species_name="Tiaratum")
    loose = [_create_animal(auth_headers, sp["id"], sex="unknown", price=350) for _ in range(5)]
    girls = [_create_animal(auth_headers, sp["id"], sex="female", price=600) for _ in range(2)]
    breeder = _create_animal(auth_headers, sp["id"], sex="female", purpose="breeder")

    # una nota de bitácora del que se va a juntar no se pierde
    from pharmatrack.models.husbandry_logs.orm import HusbandryLog
    log = HusbandryLog(species_id=sp["id"], animal_id=loose[3]["id"], log_date=date(2026, 11, 16),
                       notes="Muda")
    db_session.add(log)
    db_session.commit()

    res = client.put(f"/api/v1/species/{sp['id']}", json={"sale_format": "piece"},
                     headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text

    sale = client.get(f"{ANIMALS}?species_id={sp['id']}&page_size=100", headers=auth_headers).json()["data"]
    by_sex = {(a["purpose"], a["sex"]): a for a in sale}
    assert len(sale) == 3  # sin sexar, hembras y el pie de cría
    assert by_sex[("sale", "unknown")]["id"] == loose[0]["id"]
    assert by_sex[("sale", "unknown")]["stock"] == 5
    assert by_sex[("sale", "female")]["stock"] == 2
    assert by_sex[("breeder", "female")]["id"] == breeder["id"]

    db_session.expire_all()
    assert db_session.get(HusbandryLog, log.id).animal_id == loose[0]["id"]
