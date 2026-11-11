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
