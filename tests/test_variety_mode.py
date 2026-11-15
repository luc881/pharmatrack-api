"""Tipo de variedades de una especie: con nombre (una por ejemplar, como
Cubaris murina «Glacier») o genes combinables (varios, como un reptil)."""
from fastapi import status

from .utils import client
from .test_animals import (_make_taxonomy, _create_animal, animals_post, animals_put,
                           morphs_post, species_put)


def _two_morphs(auth_headers):
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    papaya = morphs_post(json={"species_id": sp["id"], "name": "Papaya"}, headers=auth_headers).json()
    return sp, glacier, papaya


def _set_mode(auth_headers, species_id, mode):
    return species_put(str(species_id), json={"variety_mode": mode}, headers=auth_headers)


def test_species_defaults_to_named_varieties(auth_headers):
    sp, glacier, _ = _two_morphs(auth_headers)
    assert sp["variety_mode"] == "named"
    # también viaja con el ejemplar (el sitio público lo usa para agrupar)
    animal = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]])
    assert animal["species"]["variety_mode"] == "named"


def test_named_species_takes_one_variety_per_animal(auth_headers):
    sp, glacier, papaya = _two_morphs(auth_headers)

    res = animals_post(json={"species_id": sp["id"], "sex": "female", "price": 100,
                             "price_cost": 0, "morph_ids": [glacier["id"], papaya["id"]]},
                       headers=auth_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "una sola variedad" in res.json()["detail"]

    # una o ninguna (nominal) sí
    animal = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]])
    _create_animal(auth_headers, sp["id"])

    res = animals_put(str(animal["id"]), json={"morph_ids": [glacier["id"], papaya["id"]]},
                      headers=auth_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_gene_species_combines_several(auth_headers):
    sp, glacier, papaya = _two_morphs(auth_headers)
    res = _set_mode(auth_headers, sp["id"], "genes")
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["variety_mode"] == "genes"

    animal = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"], papaya["id"]])
    assert {m["name"] for m in animal["morphs"]} == {"Glacier", "Papaya"}
    assert animal["species"]["variety_mode"] == "genes"


def test_cannot_go_back_to_named_with_combined_animals(auth_headers):
    sp, glacier, papaya = _two_morphs(auth_headers)
    _set_mode(auth_headers, sp["id"], "genes")
    animal = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"], papaya["id"]])

    res = _set_mode(auth_headers, sp["id"], "named")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert animal["code"] in res.json()["detail"]

    # con una sola variedad por ejemplar ya se puede
    animals_put(str(animal["id"]), json={"morph_ids": [glacier["id"]]}, headers=auth_headers)
    assert _set_mode(auth_headers, sp["id"], "named").status_code == status.HTTP_200_OK


def test_variety_mode_rejects_unknown_value(auth_headers):
    sp, *_ = _two_morphs(auth_headers)
    assert _set_mode(auth_headers, sp["id"], "otra").status_code == 422


def test_public_catalog_knows_the_variety_mode(auth_headers):
    """El sitio agrupa por combinación en las especies de genes."""
    sp, glacier, _ = _two_morphs(auth_headers)
    _set_mode(auth_headers, sp["id"], "genes")
    _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]])

    animal = client.get("/api/v1/public/animals").json()["data"][0]
    assert animal["species"]["variety_mode"] == "genes"
    species = client.get("/api/v1/public/species").json()
    assert species[0]["variety_mode"] == "genes"
