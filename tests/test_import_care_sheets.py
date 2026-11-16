"""scripts/import_care_sheets.py: cargar guías de cuidados desde un JSON."""
import importlib.util
from pathlib import Path

from .utils import client
from .test_animals import _make_taxonomy
from .test_care_sheets import _sheet

_spec = importlib.util.spec_from_file_location(
    "import_care_sheets", Path(__file__).resolve().parents[1] / "scripts" / "import_care_sheets.py"
)
importer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(importer)

URL = "/api/v1/care-sheets"


def _species(auth_headers, genus="Phyllium", name="Gardabagusi", group="Fásmidos"):
    *_, sp, _m = _make_taxonomy(auth_headers, group_name=f"Raíz {genus}", subgroup_name=group,
                                genus_name=genus, species_name=name)
    return sp


def _entry(species, **extra):
    return {"especie": species, "summary": "Resumen corto.", "difficulty": "sencilla", **extra}


def test_plan_reports_without_writing(auth_headers):
    with_sheet = _species(auth_headers, genus="Phyllium", name="Gardabagusi")
    without = _species(auth_headers, genus="Extatosoma", name="Tiaratum", group="Otros fasmidos")
    created = client.post(URL, json=_sheet(with_sheet), headers=auth_headers).json()

    plan = importer.plan(client, auth_headers, [
        _entry("Phyllium gardabagusi"),             # ya tiene ficha → se reemplaza
        _entry("EXTATOSOMA  tiaratum"),             # sin ficha → se crea
        _entry("Inventada inexistente"),            # no existe → error, no se crea
    ])

    assert [p["action"] for p in plan] == ["update", "create", "error"]
    assert plan[0]["sheet_id"] == created["id"]
    assert "no existe" in plan[2]["errors"][0]
    bad = importer.plan(client, auth_headers, [_entry("Extatosoma tiaratum", difficulty="más o menos")])
    assert bad[0]["action"] == "error"
    assert "Fácil, Intermedia, Difícil" in bad[0]["errors"][0]
    # no escribió nada
    assert len(client.get(URL, headers=auth_headers).json()) == 1
    assert without["id"]


def test_apply_creates_unpublished_and_keeps_existing_slug_and_state(auth_headers):
    published = _species(auth_headers, genus="Phyllium", name="Gardabagusi")
    new = _species(auth_headers, genus="Extatosoma", name="Tiaratum", group="Otros fasmidos")
    existing = client.post(URL, json={**_sheet(published), "slug": "mi-liga", "published": True},
                           headers=auth_headers).json()

    plan = importer.plan(client, auth_headers, [
        _entry("Phyllium gardabagusi", summary="Resumen nuevo."),
        _entry("Extatosoma tiaratum", body="## Lo esencial\n\nTexto."),
    ])
    results = importer.apply(client, auth_headers, plan)
    assert [r["status"] for r in results] == ["ok", "ok"]

    updated = client.get(f"{URL}/{existing['id']}", headers=auth_headers).json()
    assert updated["summary"] == "Resumen nuevo."
    assert updated["slug"] == "mi-liga" and updated["published"] is True
    assert updated["difficulty"] == "Fácil"

    sheets = {s["species_id"]: s for s in client.get(URL, headers=auth_headers).json()}
    assert sheets[new["id"]]["published"] is False


def test_too_long_text_says_which_field(auth_headers):
    _species(auth_headers, genus="Phyllium", name="Gardabagusi")
    plan = importer.plan(client, auth_headers, [_entry("Phyllium gardabagusi", habitat="x" * 2500)])
    assert plan[0]["action"] == "error"
    assert "habitat" in plan[0]["errors"][0]


def test_same_species_twice_in_the_file_is_an_error(auth_headers):
    _species(auth_headers, genus="Phyllium", name="Gardabagusi")
    plan = importer.plan(client, auth_headers, [
        _entry("Phyllium gardabagusi"), _entry("Phyllium gardabagusi"),
    ])
    assert [p["action"] for p in plan] == ["create", "error"]
    assert "repetida" in plan[1]["errors"][0]


def test_publish_flag_publishes_new_and_existing(auth_headers):
    draft = _species(auth_headers, genus="Phyllium", name="Gardabagusi")
    new = _species(auth_headers, genus="Extatosoma", name="Tiaratum", group="Otros fasmidos")
    client.post(URL, json=_sheet(draft), headers=auth_headers)  # borrador

    plan = importer.plan(client, auth_headers, [
        _entry("Phyllium gardabagusi"), _entry("Extatosoma tiaratum"),
    ], publish=True)
    importer.apply(client, auth_headers, plan)

    public = {s["species_id"] for s in client.get("/api/v1/public/care-sheets").json()}
    assert public == {draft["id"], new["id"]}
