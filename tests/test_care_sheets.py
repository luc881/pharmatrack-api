"""Fichas de cuidados: una por especie, borrador/publicada, público sin auth."""
from .utils import client
from .test_animals import _make_taxonomy, _create_animal

URL = "/api/v1/care-sheets"
PUB = "/api/v1/public/care-sheets"


def _sheet(sp, **extra):
    return {
        "species_id": sp["id"],
        "summary": "Un insecto que parece una hoja de verdad.",
        "authority": "Cumming, Bank, Le Tirant & Bradler, 2020",
        "difficulty": "Fácil",
        "taxonomy": [{"rank": "Familia", "name": "Phylliidae"},
                     {"rank": "Especie", "name": "Phyllium gardabagusi", "italic": True}],
        "facts": [{"label": "Hembra adulta", "value": "6.5–7.5 cm"}],
        "basics": ["Hojas frescas de guayaba (*Psidium guajava*)."],
        "body": "## Lo esencial\n\nTexto.",
        "photos": [{"src": "https://res.cloudinary.com/x/image/upload/a.jpg", "alt": "Hembra"}],
        "video": {"src": "https://res.cloudinary.com/x/video/upload/v.mp4", "alt": "Ninfas"},
        "references": [{"text": "ZooKeys 913: 89–126.", "url": "https://doi.org/10.3897/zookeys.913.49044"}],
        **extra,
    }


def test_care_sheet_lifecycle(auth_headers, db_session):
    _root, sub, _genus, sp, _morph = _make_taxonomy(
        auth_headers, group_name="Insectos", subgroup_name="Fásmidos",
        genus_name="Phyllium", species_name='Gardabagusi "Argopuro"',
    )
    _create_animal(auth_headers, sp["id"], code="PHY-001")

    # borrador: slug armado de la especie, no sale en el público
    res = client.post(URL, json=_sheet(sp), headers=auth_headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["slug"] == "phyllium-gardabagusi-argopuro"
    assert body["scientific_name"] == "Phyllium gardabagusi" and body["locality"] == "Argopuro"
    assert body["group"]["name"] == "Fásmidos" and body["published"] is False
    assert client.get(PUB).json() == []
    assert client.get(f"{PUB}/{body['slug']}").status_code == 404

    # una ficha por especie y slug único
    assert client.post(URL, json=_sheet(sp), headers=auth_headers).status_code == 409

    # publicar (reemplazo completo)
    put = client.put(f"{URL}/{body['id']}", json={**_sheet(sp), "slug": body["slug"], "published": True},
                     headers=auth_headers)
    assert put.status_code == 200, put.text
    row = client.get(PUB).json()[0]
    assert row["available_count"] == 1 and row["cover"].endswith("a.jpg") and "body" not in row
    detail = client.get(f"{PUB}/{body['slug']}").json()
    assert detail["facts"][0] == {"label": "Hembra adulta", "value": "6.5–7.5 cm"}
    assert detail["taxonomy"][1]["italic"] is True and detail["video"]["alt"] == "Ninfas"

    # validaciones
    bad = _sheet(sp, photos=[{"src": "javascript:alert(1)", "alt": "x"}])
    assert client.put(f"{URL}/{body['id']}", json={**bad, "slug": body["slug"]}, headers=auth_headers).status_code == 422
    assert client.post(URL, json={**_sheet(sp), "slug": "Con Espacios"}, headers=auth_headers).status_code == 422

    # sin permiso no se escribe; borrar
    assert client.post(URL, json=_sheet(sp)).status_code in (401, 403)
    assert client.delete(f"{URL}/{body['id']}", headers=auth_headers).status_code == 204
    assert client.get(PUB).json() == []
