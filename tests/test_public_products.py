"""Catálogo público de productos (show_online) y exclusión de gemelos."""
from fastapi import status

from .utils import client, route_client_factory
from .test_animals import _make_taxonomy, _create_animal

products_get, products_post, _, _, _ = route_client_factory(client, "products")


def _make_product(auth_headers, category_id, **overrides):
    payload = {
        "title": "Corteza de encino (granel)",
        "sku": "CORTEZA-PUB",
        "price_retail": 0.06,
        "price_cost": 0.02,
        "product_category_id": category_id,
        "unit_name": "g",
        "is_unit_sale": False,
        "tracks_batches": False,
        "show_online": True,
    }
    payload.update(overrides)
    res = products_post(json=payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    return res.json()


def test_public_products_only_show_online_and_no_costs(auth_headers, test_product_category):
    visible = _make_product(auth_headers, test_product_category.id)
    _make_product(
        auth_headers, test_product_category.id,
        title="Interno", sku="INTERNO-1", show_online=False,
    )

    rows = client.get("/api/v1/public/products").json()
    ids = [r["id"] for r in rows]
    assert visible["id"] in ids
    assert all(r["title"] != "Interno" for r in rows)

    row = next(r for r in rows if r["id"] == visible["id"])
    assert "price_cost" not in row
    # la categoria viaja como nombre plano para el menu lateral del sitio
    assert isinstance(row["category"], str) and row["category"]
    # venta libre: sin stock que reportar
    assert row["tracks_batches"] is False and row["stock"] is None

    # detalle publico: visible responde, interno da 404
    detail = client.get(f"/api/v1/public/products/{visible['id']}")
    assert detail.status_code == 200 and detail.json()["title"] == visible["title"]
    hidden_id = next(p["id"] for p in
                     products_get("", headers=auth_headers, params={"sku": "INTERNO-1"}).json()["data"])
    assert client.get(f"/api/v1/public/products/{hidden_id}").status_code == 404


def test_products_list_can_exclude_animal_twins(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    # Sin el filtro, el gemelo aparece (lo usa el POS para escanear)
    all_products = products_get("", headers=auth_headers, params={"page_size": 100}).json()["data"]
    assert any(p["id"] == animal["product_id"] for p in all_products)

    # Con el filtro, desaparece (lista de Productos del dashboard)
    filtered = products_get(
        "", headers=auth_headers, params={"page_size": 100, "exclude_animal_twins": True}
    ).json()["data"]
    assert all(p["id"] != animal["product_id"] for p in filtered)
