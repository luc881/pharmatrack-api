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

    # el admin sigue viéndolo todo
    admin = client.get("/api/v1/animals", headers=auth_headers).json()["data"]
    assert any(a["species"]["id"] == sp["id"] for a in admin)
