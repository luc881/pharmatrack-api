"""Manejo/cría privado de especies (husbandry_status, private_notes, threshold)."""
from .utils import client
from .test_animals import _make_taxonomy, _create_animal


def test_husbandry_fields_roundtrip_and_not_public(auth_headers, db_session):
    _root, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"])

    # default: en cultivo
    admin = client.get(f"/api/v1/species/{sp['id']}", headers=auth_headers).json()
    assert admin["husbandry_status"] == "active"
    assert admin["private_notes"] is None

    # actualizar campos privados
    res = client.put(
        f"/api/v1/species/{sp['id']}",
        json={
            "husbandry_status": "paused",
            "low_stock_threshold": 5,
            "private_notes": "Revisar humedad; separar juveniles en 2 semanas",
        },
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["husbandry_status"] == "paused"
    assert body["low_stock_threshold"] == 5
    assert "juveniles" in body["private_notes"]

    # el catálogo público NO debe exponer ninguno de los campos privados
    pub = client.get("/api/v1/public/animals").json()["data"]
    species_public = [a["species"] for a in pub if a["species"]["id"] == sp["id"]]
    assert species_public, "la especie debería aparecer en el público"
    for spub in species_public:
        assert "husbandry_status" not in spub
        assert "private_notes" not in spub
        assert "low_stock_threshold" not in spub


def test_morph_husbandry_independent_of_species_and_not_public(auth_headers, db_session):
    _root, _sub, _genus, sp, morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]])

    # el morph arranca en cultivo, igual que la especie
    admin = client.get(f"/api/v1/morphs/{morph['id']}", headers=auth_headers).json()
    assert admin["husbandry_status"] == "active"
    assert admin["private_notes"] is None

    # pausar el cultivo del morph NO toca a la especie (son independientes)
    res = client.put(
        f"/api/v1/morphs/{morph['id']}",
        json={"husbandry_status": "paused", "low_stock_threshold": 4,
              "private_notes": "Aislar esta línea"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["husbandry_status"] == "paused"
    sp_admin = client.get(f"/api/v1/species/{sp['id']}", headers=auth_headers).json()
    assert sp_admin["husbandry_status"] == "active"

    # el público (morphs embebidos en los animales) no filtra campos privados
    pub = client.get("/api/v1/public/animals").json()["data"]
    morphs_public = [m for a in pub for m in a["morphs"] if m["id"] == morph["id"]]
    assert morphs_public, "el morph debería aparecer embebido en el público"
    for mpub in morphs_public:
        assert "husbandry_status" not in mpub
        assert "private_notes" not in mpub
        assert "low_stock_threshold" not in mpub
