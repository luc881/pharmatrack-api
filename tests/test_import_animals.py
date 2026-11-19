"""scripts/import_animals.py: alta de animales y productos de otro expositor."""
import importlib.util
from pathlib import Path

from .utils import client
from .test_animals import _make_taxonomy

_spec = importlib.util.spec_from_file_location(
    "import_animals", Path(__file__).resolve().parents[1] / "scripts" / "import_animals.py"
)
importer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(importer)


def _data():
    return {
        "proveedor": "BD Import",
        "especies_nuevas": {"Heterodon platirhinos": {"grupo": "Culebras", "nombre_comun": "Hognose"}},
        "animales": [
            {"codigo": "BDI-01", "especie": "Python regius", "sexo": "macho", "precio": 30000,
             "variedad": ["Clown", "Het Hypo"]},
            {"codigo": "BDI-02", "especie": "heterodon  platirhinos", "sexo": "hembra", "precio": 2500,
             "descripcion": "Nominal"},
            {"codigo": "BDI-03", "especie": "Python regius", "sexo": "hembra", "precio": None},
        ],
        "productos": [{"nombre": "Slush BDI", "precio": 50, "categoria": "Bebidas BDI", "se_prepara": True}],
    }


def _codes(auth_headers):
    res = client.get("/api/v1/animals?page_size=500", headers=auth_headers).json()["data"]
    return {a["code"]: a for a in res if a["code"].startswith("BDI-")}


def test_review_then_apply_then_rerun(auth_headers):
    owner = client.post("/api/v1/suppliers", json={"name": "BD Import"}, headers=auth_headers).json()
    *_, python, _m = _make_taxonomy(auth_headers, group_name="Reptiles BDI", subgroup_name="Culebras",
                                    genus_name="Python", species_name="Regius", morph_name="Clown")
    lines = []

    # revisión: dice qué haría y no escribe nada
    counts = importer.Importer(client, auth_headers, _data(), log=lines.append).run()
    assert counts == {"creados": 3, "ya estaban": 0, "con error": 1}
    assert any("falta el precio" in line for line in lines)
    assert any("a «genes»" in line for line in lines)
    assert _codes(auth_headers) == {}

    # de verdad
    counts = importer.Importer(client, auth_headers, _data(), apply=True, log=lines.append).run()
    assert counts == {"creados": 3, "ya estaban": 0, "con error": 1}
    animals = _codes(auth_headers)
    assert set(animals) == {"BDI-01", "BDI-02"}
    bp = animals["BDI-01"]
    assert bp["consignor_id"] == owner["id"] and bp["quick_sale"] and not bp["show_public"]
    assert sorted(m["name"] for m in bp["morphs"]) == ["Clown", "Het Hypo"]  # Clown ya existía
    assert client.get(f"/api/v1/species/{python['id']}", headers=auth_headers).json()["variety_mode"] == "genes"
    assert animals["BDI-02"]["species"]["common_name"] == "Hognose"

    slush = client.get("/api/v1/products?search=Slush BDI", headers=auth_headers).json()["data"]
    assert [(p["consignor_id"], p["quick_sale"], p["needs_prep"]) for p in slush] == [(owner["id"], True, True)]

    # otra vez: no duplica
    counts = importer.Importer(client, auth_headers, _data(), apply=True, log=lines.append).run()
    assert counts == {"creados": 0, "ya estaban": 3, "con error": 1}


def test_unknown_supplier_stops(auth_headers):
    counts = importer.Importer(client, auth_headers, {**_data(), "proveedor": "Nadie"}, log=lambda _: None).run()
    assert counts == {"creados": 0, "ya estaban": 0, "con error": 1}
