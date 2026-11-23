"""POST /sales/checkout: la venta completa en una transacción."""
from fastapi import status

from pharmatrack.models.sale_payments.orm import SalePayment
from pharmatrack.models.sales.orm import Sale

from .utils import client

URL = "/api/v1/sales/checkout"


def _body(branch, product, quantity="3", **extra):
    return {
        "branch_id": branch.id,
        "items": [{"product_id": product.id, "quantity": quantity}],
        "payments": [{"method_payment": "cash", "amount": "500.00"}],
        **extra,
    }


def test_checkout_registra_y_completa(auth_headers, test_branch, test_product,
                                      test_product_batch, db_session,
                                      test_user_with_role_permissions_branch_auth):
    response = client.post(URL, json=_body(test_branch, test_product), headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["status"] == "completed"
    assert float(data["total"]) > 0
    # el vendedor sale del token, no del cuerpo
    assert data["user_id"] == test_user_with_role_permissions_branch_auth.id

    db_session.refresh(test_product_batch)
    assert test_product_batch.quantity == 97
    assert db_session.query(SalePayment).filter_by(sale_id=data["id"]).count() == 1


def test_checkout_repetido_devuelve_la_misma_venta(auth_headers, test_branch, test_product,
                                                   test_product_batch, db_session):
    body = _body(test_branch, test_product, idempotency_key="venta-de-prueba-0001")
    first = client.post(URL, json=body, headers=auth_headers)
    second = client.post(URL, json=body, headers=auth_headers)
    assert first.status_code == second.status_code == status.HTTP_201_CREATED
    assert first.json()["id"] == second.json()["id"]

    assert db_session.query(Sale).count() == 1
    db_session.refresh(test_product_batch)
    assert test_product_batch.quantity == 97  # el stock se descontó una sola vez


def test_checkout_sin_stock_no_deja_nada(auth_headers, test_branch, test_product,
                                         test_product_batch, db_session):
    body = _body(test_branch, test_product, quantity="101", idempotency_key="venta-de-prueba-0002")
    response = client.post(URL, json=body, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Stock insuficiente" in response.json()["detail"]

    db_session.rollback()  # el test comparte sesión con el API
    assert db_session.query(Sale).count() == 0
    assert db_session.query(SalePayment).count() == 0
    db_session.refresh(test_product_batch)
    assert test_product_batch.quantity == 100


def test_checkout_sin_lineas(auth_headers, test_branch):
    response = client.post(URL, json={"branch_id": test_branch.id, "items": []}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_checkout_sin_auth(test_branch, test_product):
    response = client.post(URL, json=_body(test_branch, test_product))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================
# sold_at: la hora real de una venta que se sube después
# =========================================================
def test_checkout_guarda_sold_at(auth_headers, test_branch, test_product, test_product_batch):
    body = _body(test_branch, test_product, sold_at="2026-11-13T18:30:00Z")
    res = client.post(URL, json=body, headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    assert res.json()["date_sale"] == "2026-11-13T18:30:00+00:00"


def test_checkout_convierte_sold_at_a_utc(auth_headers, test_branch, test_product, test_product_batch):
    body = _body(test_branch, test_product, sold_at="2026-11-13T12:30:00-06:00")
    res = client.post(URL, json=body, headers=auth_headers)
    assert res.json()["date_sale"] == "2026-11-13T18:30:00+00:00"


def test_checkout_con_reloj_adelantado_usa_la_hora_del_servidor(auth_headers, test_branch, test_product, test_product_batch):
    """Un equipo con el reloj adelantado no puede dejar sin registrar una venta
    ya cobrada: la hora se recorta a la del servidor."""
    from datetime import datetime, timedelta, timezone

    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    res = client.post(URL, json=_body(test_branch, test_product, sold_at=future), headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    sold = datetime.fromisoformat(res.json()["date_sale"])
    now = datetime.now(timezone.utc)
    assert abs(now - sold) < timedelta(minutes=5)


def test_checkout_sin_sold_at_usa_la_hora_actual(auth_headers, test_branch, test_product, test_product_batch):
    from datetime import datetime, timedelta, timezone

    res = client.post(URL, json=_body(test_branch, test_product), headers=auth_headers)
    sold = datetime.fromisoformat(res.json()["date_sale"])
    now = datetime.now(timezone.utc)
    assert abs(now - sold) < timedelta(minutes=5)


# =========================================================
# Lo que la venta rápida da por hecho al calcular su total
# =========================================================
def test_checkout_redondea_el_impuesto_por_linea(auth_headers, test_branch,
                                                     test_product_category, db_session):
    """Dos líneas de $10.03 al 16 %: 1.60 + 1.60 = 3.20 (no 3.2096 → 3.21).
    quick-sale-math.js del dashboard redondea igual."""
    from pharmatrack.models.products.orm import Product
    from .test_bundles import _make_product, _add_batch

    ids = []
    for sku in ("T1", "T2"):
        p = _make_product(auth_headers, test_product_category.id, sku=sku, price_retail=10.03)
        _add_batch(db_session, p["id"], 5)
        ids.append(p["id"])
    db_session.query(Product).filter(Product.id.in_(ids)).update(
        {"tax_percentage": 16}, synchronize_session=False)
    db_session.commit()

    res = client.post(URL, headers=auth_headers, json={
        "branch_id": test_branch.id,
        "items": [{"product_id": i, "quantity": "1"} for i in ids],
        "payments": [{"method_payment": "cash", "amount": "23.26"}],
    })
    assert res.status_code == status.HTTP_201_CREATED, res.text
    data = res.json()
    assert float(data["subtotal"]) == 20.06
    assert float(data["tax"]) == 3.20
    assert float(data["total"]) == 23.26


def test_checkout_de_cero_pesos_va_sin_pagos(auth_headers, test_branch, test_product,
                                             test_product_batch, db_session):
    """Descuento del 100 %: no hay pago que mandar (un pago debe ser > 0)."""
    price = float(test_product.price_retail)
    res = client.post(URL, headers=auth_headers, json={
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": "1", "discount": price}],
        "payments": [],
    })
    assert res.status_code == status.HTTP_201_CREATED, res.text
    assert float(res.json()["total"]) == 0


def _admin_headers(user, role="admin"):
    from datetime import timedelta
    from pharmatrack.utils.security import create_jwt_token
    token = create_jwt_token(username=user.email, user_id=user.id, role=role,
                             expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


def test_checkout_precio_al_vuelo_de_un_admin(test_branch, test_product, test_product_batch,
                                              test_user_with_role_permissions_branch_auth,
                                              db_session):
    """La venta rápida deja a un admin cobrar a otro precio (sin tocar el producto)."""
    body = _body(test_branch, test_product)
    body["items"][0]["unit_price"] = "150.00"
    res = client.post(URL, json=body,
                      headers=_admin_headers(test_user_with_role_permissions_branch_auth))
    assert res.status_code == status.HTTP_201_CREATED, res.text
    from pharmatrack.models.sale_details.orm import SaleDetail
    detail = db_session.query(SaleDetail).filter_by(sale_id=res.json()["id"]).one()
    assert float(detail.price_unit) == 150
    assert float(res.json()["subtotal"]) == 450
    assert float(test_product.price_retail) == 20


def test_checkout_precio_al_vuelo_de_un_superadmin(test_branch, test_product, test_product_batch,
                                                   test_user_with_role_permissions_branch_auth):
    body = _body(test_branch, test_product)
    body["items"][0]["unit_price"] = "150.00"
    res = client.post(URL, json=body, headers=_admin_headers(
        test_user_with_role_permissions_branch_auth, role="superadmin"))
    assert res.status_code == status.HTTP_201_CREATED, res.text


def test_checkout_precio_al_vuelo_solo_admin(auth_headers, test_branch, test_product,
                                             test_product_batch, db_session):
    body = _body(test_branch, test_product)
    body["items"][0]["unit_price"] = "1.00"
    res = client.post(URL, json=body, headers=auth_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN, res.text
    assert db_session.query(Sale).count() == 0
