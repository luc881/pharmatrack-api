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
