"""Visibilidad pública por grupo raíz (show_public)."""
from .utils import client
from .test_animals import _make_taxonomy, _create_animal


def test_hidden_root_group_disappears_from_public(auth_headers, db_session):
    # animal cuelga de root -> sub -> genus -> species; ocultar root debe cascada
    group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"])

    # visible por defecto: aparece en grupos y animales públicos
    groups = client.get("/api/v1/public/animals/groups").json()
    assert any(g["id"] == group["id"] for g in groups)
    animals = client.get("/api/v1/public/animals").json()["data"]
    assert any(a["species"]["id"] == sp["id"] for a in animals)

    # ocultar el grupo raíz
    res = client.put(f"/api/v1/animal-groups/{group['id']}",
                     json={"show_public": False}, headers=auth_headers)
    assert res.status_code == 200, res.text
    assert res.json()["show_public"] is False

    # ya no aparece en grupos ni en el listado público
    groups = client.get("/api/v1/public/animals/groups").json()
    assert not any(g["id"] == group["id"] for g in groups)
    animals = client.get("/api/v1/public/animals").json()["data"]
    assert not any(a["species"]["id"] == sp["id"] for a in animals)

    # el detalle por link directo tampoco debe mostrarlo (404)
    admin_animals = client.get("/api/v1/animals", headers=auth_headers,
                               params={"species_id": sp["id"]}).json()["data"]
    assert client.get(f"/api/v1/public/animals/{admin_animals[0]['id']}").status_code == 404

    # el admin sigue viéndolo todo
    admin = client.get("/api/v1/animals", headers=auth_headers).json()["data"]
    assert any(a["species"]["id"] == sp["id"] for a in admin)


def test_feature_home_flag_roundtrip(auth_headers):
    group, _sub, _genus, _sp, _morph = _make_taxonomy(auth_headers)
    # por defecto no destacado
    assert group["feature_home"] is False

    res = client.put(f"/api/v1/animal-groups/{group['id']}",
                     json={"feature_home": True}, headers=auth_headers)
    assert res.status_code == 200, res.text
    assert res.json()["feature_home"] is True

    # se refleja en el listado público de grupos
    groups = client.get("/api/v1/public/animals/groups").json()
    hit = next(g for g in groups if g["id"] == group["id"])
    assert hit["feature_home"] is True


def test_site_settings_roundtrip(auth_headers):
    # lectura pública (sin auth)
    res = client.get("/api/v1/settings/site")
    assert res.status_code == 200, res.text
    assert res.json()["show_category_browse"] is True

    # admin apaga la sección de explorar por categorías
    res = client.put("/api/v1/settings/site",
                     json={"show_category_browse": False}, headers=auth_headers)
    assert res.status_code == 200, res.text
    assert client.get("/api/v1/settings/site").json()["show_category_browse"] is False
