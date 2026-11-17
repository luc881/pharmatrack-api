"""Venta rápida: bandera en el producto y catálogo en una sola petición."""
from fastapi import status

from .utils import client
from .test_bundles import _make_product, _add_batch

CATALOG = "/api/v1/products/quick-sale"


def test_quick_sale_defaults_false_and_toggles(auth_headers, test_product_category):
    p = _make_product(auth_headers, test_product_category.id)
    assert p["quick_sale"] is False

    res = client.patch(f"/api/v1/products/{p['id']}/toggle-quick-sale", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["quick_sale"] is True


def test_list_filters_by_quick_sale(auth_headers, test_product_category):
    a = _make_product(auth_headers, test_product_category.id, sku="A1", quick_sale=True)
    _make_product(auth_headers, test_product_category.id, sku="B1", title="Otro")

    res = client.get("/api/v1/products?quick_sale=true", headers=auth_headers)
    assert [p["id"] for p in res.json()["data"]] == [a["id"]]


def test_quick_sale_catalog_stock_and_bundle(auth_headers, test_product_category, db_session):
    cueva = _make_product(auth_headers, test_product_category.id, sku="C1", quick_sale=True,
                          max_discount=10)
    # El impuesto no se captura por el API (columna heredada); se fija directo
    from pharmatrack.models.products.orm import Product
    db_session.query(Product).filter_by(id=cueva["id"]).update({"tax_percentage": 16})
    db_session.commit()
    _add_batch(db_session, cueva["id"], 5)
    _add_batch(db_session, cueva["id"], 3)
    pack = _make_product(auth_headers, test_product_category.id, sku="P1", title="3 cuevas",
                         quick_sale=True, tracks_batches=False, price_retail=200)
    res = client.put(f"/api/v1/products/{pack['id']}/bundle-items",
                     json=[{"component_product_id": cueva["id"], "quantity": 3}],
                     headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    _make_product(auth_headers, test_product_category.id, sku="X1", title="No marcado")

    res = client.get(CATALOG, headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    items = {i["id"]: i for i in res.json()}

    assert set(items) == {cueva["id"], pack["id"]}
    c = items[cueva["id"]]
    assert c["stock"] == 8
    assert c["max_discount"] == 10
    assert c["tax_percentage"] == 16
    assert float(c["price_retail"]) == 80
    assert c["category"] == test_product_category.name
    assert c["is_bundle"] is False and c["components"] == []
    assert c["blocked_reason"] is None and c["animal"] is None

    p = items[pack["id"]]
    assert p["is_bundle"] is True and p["stock"] is None
    assert p["components"] == [{"product_id": cueva["id"], "quantity": 3, "stock": 8}]


def test_quick_sale_catalog_skips_inactive(auth_headers, test_product_category):
    p = _make_product(auth_headers, test_product_category.id, sku="I1", quick_sale=True)
    client.patch(f"/api/v1/products/{p['id']}/toggle-active", headers=auth_headers)
    assert client.get(CATALOG, headers=auth_headers).json() == []


def test_quick_sale_catalog_untracked_product_has_no_stock(auth_headers, test_product_category):
    p = _make_product(auth_headers, test_product_category.id, sku="G1", quick_sale=True,
                      tracks_batches=False)
    item = client.get(CATALOG, headers=auth_headers).json()[0]
    assert item["id"] == p["id"] and item["stock"] is None and item["is_bundle"] is False


def test_quick_sale_catalog_blocks_reserved_animal(auth_headers):
    from .test_animals import _make_taxonomy, _create_animal, animals_put

    *_, sp, _morph = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    client.patch(f"/api/v1/products/{animal['product_id']}/toggle-quick-sale", headers=auth_headers)

    item = client.get(CATALOG, headers=auth_headers).json()[0]
    assert item["blocked_reason"] is None
    assert item["animal"]["id"] == animal["id"]
    assert item["animal"]["species"]["name"] == sp["name"]
    assert item["stock"] == 1

    res = animals_put(str(animal["id"]), json={"status": "reserved"}, headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    item = client.get(CATALOG, headers=auth_headers).json()[0]
    assert item["blocked_reason"] == "reserved"


def test_quick_sale_catalog_requires_login():
    assert client.get(CATALOG).status_code in (401, 403)


def test_quick_sale_catalog_no_consulta_por_animal(auth_headers, db_session):
    """El número de consultas no crece con los animales marcados."""
    from sqlalchemy import event
    from .utils import engine
    from .test_animals import _make_taxonomy, _create_animal

    *_, sp, morph = _make_taxonomy(auth_headers)

    def add_animal():
        animal = _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]])
        client.patch(f"/api/v1/products/{animal['product_id']}/toggle-quick-sale",
                     headers=auth_headers)

    def queries():
        db_session.expunge_all()
        seen = []
        listener = lambda *args: seen.append(args[2])  # noqa: E731
        event.listen(engine, "before_cursor_execute", listener)
        try:
            res = client.get(CATALOG, headers=auth_headers)
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        assert res.status_code == status.HTTP_200_OK, res.text
        return len(seen), len(res.json())

    add_animal()
    one, count = queries()
    assert count == 1
    add_animal()
    add_animal()
    three, count = queries()
    assert count == 3
    assert three == one


def test_animal_can_be_created_already_in_quick_sale(auth_headers):
    """«Poner en venta» con «También en venta rápida»: los gemelos nacen marcados."""
    from .test_animals import _make_taxonomy, _create_animal

    *_, sp, _morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], count=3, quick_sale=True)
    _create_animal(auth_headers, sp["id"])  # sin marcar: no entra

    items = client.get(CATALOG, headers=auth_headers).json()
    assert len(items) == 3
    assert all(i["animal"]["species"]["id"] == sp["id"] for i in items)


def test_several_products_without_sku(auth_headers, test_product_category):
    """El SKU es opcional: dos productos sin SKU no son «duplicados»."""
    first = _make_product(auth_headers, test_product_category.id, sku=None, title="Sin código uno")
    second = _make_product(auth_headers, test_product_category.id, sku=None, title="Sin código dos")
    assert first["id"] != second["id"]


def test_animal_owner_lives_in_its_twin(auth_headers):
    """El dueño de un animal (otro expositor) va en su producto gemelo: su ticket sale aparte."""
    from .test_animals import _make_taxonomy, _create_animal

    owner = client.post("/api/v1/suppliers", json={"name": "BD Exóticos"}, headers=auth_headers).json()
    *_, sp, _morph = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"], quick_sale=True)
    assert animal["consignor_id"] is None

    res = client.put(f"/api/v1/animals/{animal['id']}", json={"consignor_id": owner["id"]},
                     headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["consignor_id"] == owner["id"]
    item = next(i for i in client.get(CATALOG, headers=auth_headers).json()
                if i["id"] == animal["product_id"])
    assert item["consignor_id"] == owner["id"]

    # otro cambio no lo borra; null lo regresa a propio; un dueño que no existe no
    client.put(f"/api/v1/animals/{animal['id']}", json={"price": 999}, headers=auth_headers)
    assert client.get(f"/api/v1/animals/{animal['id']}", headers=auth_headers).json()["consignor_id"] == owner["id"]
    assert client.put(f"/api/v1/animals/{animal['id']}", json={"consignor_id": 999999},
                      headers=auth_headers).status_code == status.HTTP_400_BAD_REQUEST
    res = client.put(f"/api/v1/animals/{animal['id']}", json={"consignor_id": None}, headers=auth_headers)
    assert res.json()["consignor_id"] is None
