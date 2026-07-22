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


def test_group_tree_keeps_flags(auth_headers):
    """El arbol debe traer show_public y feature_home: se armaba campo por
    campo y esos dos se quedaban fuera, asi que el dashboard los veia con su
    valor por defecto aunque en la BD estuvieran marcados."""
    group, sub, _genus, _sp, _morph = _make_taxonomy(auth_headers)
    client.put(f"/api/v1/animal-groups/{group['id']}", headers=auth_headers,
               json={"show_public": False})
    client.put(f"/api/v1/animal-groups/{sub['id']}", headers=auth_headers,
               json={"feature_home": True})

    tree = client.get("/api/v1/animal-groups/tree", headers=auth_headers).json()
    root = next(g for g in tree if g["id"] == group["id"])
    assert root["show_public"] is False
    child = next(c for c in root["children"] if c["id"] == sub["id"])
    assert child["feature_home"] is True


def test_show_in_nav_is_independent_from_show_public(auth_headers):
    """Quitar un grupo del menu no lo saca del sitio: sus animales se siguen
    vendiendo y puede destacarse en la home."""
    group, _sub, _genus, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"])

    res = client.put(f"/api/v1/animal-groups/{group['id']}", headers=auth_headers,
                     json={"show_in_nav": False})
    assert res.status_code == 200, res.text
    assert res.json()["show_in_nav"] is False
    assert res.json()["show_public"] is True

    # sigue en la API publica (el menu lo filtra el sitio, no el backend)
    groups = client.get("/api/v1/public/animals/groups").json()
    hit = next(g for g in groups if g["id"] == group["id"])
    assert hit["show_in_nav"] is False

    # y sus animales se siguen publicando
    animals = client.get("/api/v1/public/animals",
                         params={"species_id": sp["id"]}).json()["data"]
    assert len(animals) == 1

    # el arbol tambien lo refleja
    tree = client.get("/api/v1/animal-groups/tree", headers=auth_headers).json()
    assert next(g for g in tree if g["id"] == group["id"])["show_in_nav"] is False
