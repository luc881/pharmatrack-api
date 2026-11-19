"""scripts/corregir_variedades.py: arreglar animales dados de alta con «het» como variedad."""
import importlib.util
from pathlib import Path

from .utils import client
from .test_animals import _make_taxonomy

_root = Path(__file__).resolve().parents[1] / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _root / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


importer, fixer = _load("import_animals"), _load("corregir_variedades")


def test_het_goes_to_description_names_get_quotes_and_loose_hets_are_deleted(auth_headers):
    client.post("/api/v1/suppliers", json={"name": "BD Fix"}, headers=auth_headers)
    *_, python, _m = _make_taxonomy(auth_headers, group_name="Reptiles FIX", subgroup_name="Culebras FIX",
                                    genus_name="Python", species_name="Regius", morph_name="'Pastel'")
    # como se corrió: het como variedad y nombres sin comillas
    old = {"proveedor": "BD Fix", "animales": [
        {"codigo": "FX-01", "especie": "Python regius", "sexo": "macho", "precio": 100,
         "variedad": ["Clown", "Het Hypo"]},
        {"codigo": "FX-02", "especie": "Python regius", "sexo": "macho", "precio": 100,
         "variedad": ["Pastel", "Het Clown"], "descripcion": "Bonito"},
    ]}
    importer.Importer(client, auth_headers, old, apply=True, log=lambda _: None).run()
    other = client.post("/api/v1/animals", json={  # alguien más usa Het Clown: no se borra
        "species_id": python["id"], "sex": "female", "price": 1,
        "morph_ids": [m["id"] for m in client.get(f"/api/v1/morphs?species_id={python['id']}",
                                                  headers=auth_headers).json()["data"] if m["name"] == "Het Clown"],
    }, headers=auth_headers).json()

    new = {"animales": [
        {"codigo": "FX-01", "especie": "Python regius", "variedad": ["'Clown'"], "descripcion": "Het Hypo"},
        {"codigo": "FX-02", "especie": "Python regius", "variedad": ["'Pastel'"], "descripcion": "Bonito. Het Clown"},
    ]}
    lines = []
    review = fixer.run(client, auth_headers, new, log=lines.append)
    assert review["con error"] == 0
    assert any("borrar variedad Het Hypo" in line for line in lines)
    assert not any("borrar variedad Het Clown" in line for line in lines)

    fixer.run(client, auth_headers, new, apply=True, log=lambda _: None)
    animals = {a["code"]: a for a in client.get("/api/v1/animals?page_size=500", headers=auth_headers).json()["data"]}
    assert [m["name"] for m in animals["FX-01"]["morphs"]] == ["'Clown'"]
    assert animals["FX-01"]["description"] == "Het Hypo"
    assert [m["name"] for m in animals["FX-02"]["morphs"]] == ["'Pastel'"]
    assert animals["FX-02"]["description"] == "Bonito. Het Clown"
    names = sorted(m["name"] for m in client.get(f"/api/v1/morphs?species_id={python['id']}",
                                                 headers=auth_headers).json()["data"])
    assert names == ["'Clown'", "'Pastel'", "Het Clown"]  # Het Clown lo sigue usando otro animal
    assert other["id"]

    # otra vez: nada que hacer
    assert fixer.run(client, auth_headers, new, apply=True, log=lambda _: None) == {"cambios": 0, "con error": 0}
