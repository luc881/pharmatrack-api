"""Dificultad y rareza: opciones fijas, con sinónimos traducidos."""
from fastapi import status

from pharmatrack.types.levels import normalize_difficulty, normalize_rarity

from .utils import client
from .test_animals import _make_taxonomy, species_put


def test_synonyms_become_the_fixed_option():
    assert normalize_difficulty("sencilla") == "Fácil"
    assert normalize_difficulty("  PRINCIPIANTE ") == "Fácil"
    assert normalize_difficulty("Avanzado") == "Difícil"
    assert normalize_difficulty("intermedio") == "Intermedia"
    assert normalize_rarity("poco") == "Poco común"
    assert normalize_rarity("muy comun") == "Común"
    assert normalize_rarity("Rarísima") == "Muy rara"
    assert normalize_difficulty("algo raro") is None
    assert normalize_difficulty("") is None


def test_species_saves_the_fixed_option(auth_headers):
    *_, sp, _m = _make_taxonomy(auth_headers)
    res = species_put(f"/{sp['id']}", json={"difficulty": "sencilla", "rarity": "poco común"},
                      headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["difficulty"] == "Fácil"
    assert res.json()["rarity"] == "Poco común"

    # vacío = sin dato
    res = species_put(f"/{sp['id']}", json={"difficulty": "", "rarity": None}, headers=auth_headers)
    assert res.json()["difficulty"] is None and res.json()["rarity"] is None


def test_unknown_value_says_which_options_exist(auth_headers):
    *_, sp, _m = _make_taxonomy(auth_headers)
    res = species_put(f"/{sp['id']}", json={"difficulty": "más o menos"}, headers=auth_headers)
    assert res.status_code == 422
    assert "Fácil, Intermedia, Difícil" in res.text


def test_care_sheet_difficulty_is_normalized_too(auth_headers):
    *_, sp, _m = _make_taxonomy(auth_headers)
    from .test_care_sheets import _sheet
    res = client.post("/api/v1/care-sheets", json=_sheet(sp, difficulty="principiante"),
                      headers=auth_headers)
    assert res.status_code in (200, 201), res.text
    assert res.json()["difficulty"] == "Fácil"
