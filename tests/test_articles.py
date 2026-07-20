"""Artículos: CRUD admin + el público solo ve publicados."""
from fastapi import status

from .utils import client, route_client_factory

articles_get, articles_post, articles_put, _, articles_delete = route_client_factory(client, "articles")


def _payload(**overrides):
    base = {
        "title": "Guía básica para tu primera tarántula",
        "category": "Cuidados",
        "excerpt": "Todo lo que necesitas antes de traerla a casa.",
        "body": "Intro del artículo.\n\n## El terrario\n\nPárrafo del terrario.\n\n> Una cita destacada.",
        "author_name": "Opuntia Den",
        "author_role": "Criadora",
        "tags": ["tarántulas", "principiantes"],
        "published": False,
    }
    base.update(overrides)
    return base


def test_crud_and_publish_flow(auth_headers):
    # crear como borrador
    res = articles_post(json=_payload(), headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    article = res.json()
    assert article["published"] is False and article["published_at"] is None
    assert article["reading_minutes"] >= 1

    # el público NO ve borradores
    public = client.get("/api/v1/public/articles").json()
    assert all(a["id"] != article["id"] for a in public)
    assert client.get(f"/api/v1/public/articles/{article['id']}").status_code == 404

    # publicar
    res = articles_put(str(article["id"]), json={"published": True}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["published"] is True and res.json()["published_at"]

    # el público ya lo ve (lista y detalle)
    public = client.get("/api/v1/public/articles").json()
    assert any(a["id"] == article["id"] for a in public)
    detail = client.get(f"/api/v1/public/articles/{article['id']}").json()
    assert detail["title"] == article["title"]
    assert detail["tags"] == ["tarántulas", "principiantes"]

    # despublicar conserva el contenido pero lo oculta
    articles_put(str(article["id"]), json={"published": False}, headers=auth_headers)
    assert client.get(f"/api/v1/public/articles/{article['id']}").status_code == 404

    # borrar
    assert articles_delete(str(article["id"]), headers=auth_headers).status_code == 204


def test_admin_requires_auth():
    assert articles_get().status_code in (401, 403)
    assert articles_post(json=_payload()).status_code in (401, 403)
