"""Paquetes (bundles), ofertas (compare_at_price) y tope de descuento."""
from decimal import Decimal

from fastapi import status

from .utils import client, route_client_factory
from .test_animals import _make_taxonomy, _create_animal, animals_get

products_get, products_post, products_put, _, _ = route_client_factory(client, "products")


def _make_product(auth_headers, category_id, **overrides):
    payload = {
        "title": "Cueva de resina",
        "sku": overrides.pop("sku", "CUEVA-B"),
        "price_retail": 80,
        "price_cost": 35,
        "product_category_id": category_id,
        "unit_name": "pieza",
        "tracks_batches": True,
    }
    payload.update(overrides)
    res = products_post(json=payload, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    return res.json()


def _add_batch(db_session, product_id, quantity):
    from pharmatrack.models.product_batch.orm import ProductBatch

    batch = ProductBatch(product_id=product_id, quantity=quantity, purchase_price=10)
    db_session.add(batch)
    db_session.commit()
    return batch


def _draft_sale(db_session, user, branch, product_id, quantity, price, discount=0):
    from pharmatrack.models.sales.orm import Sale
    from pharmatrack.models.sale_details.orm import SaleDetail

    sale = Sale(user_id=user.id, branch_id=branch.id, status="draft",
                subtotal=0, tax=0, discount=0, total=0)
    db_session.add(sale)
    db_session.commit()
    db_session.add(SaleDetail(
        sale_id=sale.id, product_id=product_id, quantity=Decimal(quantity),
        price_unit=Decimal(price), discount=Decimal(discount), tax=Decimal("0"),
        total=Decimal(price) * quantity - Decimal(discount),
    ))
    db_session.commit()
    return sale


# =========================================================
# Descuentos
# =========================================================
def test_max_discount_via_detail_endpoint(
    auth_headers, test_product_category, db_session,
    test_user_with_role_permissions_branch_auth, test_branch,
):
    from pharmatrack.models.sales.orm import Sale

    product = _make_product(
        auth_headers, test_product_category.id,
        sku="DESC-2", price_retail=100, max_discount=10,
    )
    sale = Sale(
        user_id=test_user_with_role_permissions_branch_auth.id,
        branch_id=test_branch.id, status="draft",
        subtotal=0, tax=0, discount=0, total=0,
    )
    db_session.add(sale)
    db_session.commit()

    base = {"sale_id": sale.id, "product_id": product["id"], "quantity": 1}

    res = client.post("/api/v1/saledetails", json={**base, "discount": 50}, headers=auth_headers)
    assert res.status_code == 400
    assert "descuento máximo" in res.json()["detail"].lower()

    res = client.post("/api/v1/saledetails", json={**base, "discount": 8}, headers=auth_headers)
    assert res.status_code in (200, 201), res.text


# =========================================================
# Ofertas (compare_at_price)
# =========================================================
def test_compare_at_price_flows_to_public(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)

    # oferta inválida: precio anterior menor o igual al actual
    from .test_animals import animals_post
    res = animals_post(
        json={"species_id": sp["id"], "sex": "female", "price": 3500.0,
              "price_cost": 100.0, "morph_ids": [], "compare_at_price": 3000.0},
        headers=auth_headers,
    )
    assert res.status_code == 400

    animal = _create_animal(auth_headers, sp["id"], compare_at_price=4200.0)
    assert animal["compare_at_price"] == 4200.0

    # el sitio público la ve
    row = next(a for a in client.get("/api/v1/public/animals").json()["data"]
               if a["id"] == animal["id"])
    assert row["compare_at_price"] == 4200.0


# =========================================================
# Paquetes
# =========================================================
def test_bundle_sale_discounts_components_and_marks_animal(
    auth_headers, test_product_category, db_session,
    test_user_with_role_permissions_branch_auth, test_branch,
):
    from pharmatrack.models.product_batch.orm import ProductBatch

    # componente 1: animal individual (gemelo con lote de 1)
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    # componente 2: producto con stock 5
    comp = _make_product(auth_headers, test_product_category.id, sku="COMP-1")
    _add_batch(db_session, comp["id"], 5)

    # componente 3: venta libre (no limita ni descuenta)
    granel = _make_product(
        auth_headers, test_product_category.id,
        sku="GRANEL-1", tracks_batches=False, unit_name="g", price_retail=0.06,
    )

    # el paquete: producto sin stock propio
    bundle = _make_product(
        auth_headers, test_product_category.id,
        sku="KIT-1", title="Kit inicio tarántula", tracks_batches=False,
        price_retail=3800, compare_at_price=4000,
    )
    res = products_put(
        f"{bundle['id']}/bundle-items",
        json=[
            {"component_product_id": animal["product_id"], "quantity": 1},
            {"component_product_id": comp["id"], "quantity": 2},
            {"component_product_id": granel["id"], "quantity": 1},
        ],
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert len(res.json()) == 3

    # anidamiento prohibido en ambos sentidos
    other = _make_product(auth_headers, test_product_category.id, sku="KIT-2", tracks_batches=False)
    res = products_put(
        f"{other['id']}/bundle-items",
        json=[{"component_product_id": bundle["id"], "quantity": 1}],
        headers=auth_headers,
    )
    assert res.status_code == 400

    # el público ve el paquete con componentes y stock derivado
    # (animal 1, comp 5//2=2 → min = 1)
    from pharmatrack.models.products.orm import Product
    db_session.query(Product).filter(Product.id == bundle["id"]).update({Product.show_online: True})
    db_session.commit()
    pub = client.get(f"/api/v1/public/products/{bundle['id']}").json()
    assert pub["is_bundle"] is True and len(pub["components"]) == 3
    assert pub["stock"] == 1 and pub["compare_at_price"] == 4000

    # vender el paquete: descuenta componentes y marca el animal vendido
    sale = _draft_sale(
        db_session, test_user_with_role_permissions_branch_auth, test_branch,
        bundle["id"], 1, 3800,
    )
    res = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert res.status_code == 200, res.text

    comp_stock = db_session.query(ProductBatch).filter_by(product_id=comp["id"]).first()
    db_session.refresh(comp_stock)
    assert comp_stock.quantity == 3  # 5 - 2

    refreshed = animals_get(str(animal["id"]), headers=auth_headers).json()
    assert refreshed["status"] == "sold"

    # sin stock del animal, el paquete queda agotado para el público
    pub = client.get(f"/api/v1/public/products/{bundle['id']}").json()
    assert pub["stock"] == 0
