"""Cada cambio de stock deja una fila en stock_movements."""
from pharmatrack.models.stock_movements.orm import StockMovement

from .utils import client


def _movements(db_session, batch):
    return (db_session.query(StockMovement)
            .filter_by(batch_id=batch.id).order_by(StockMovement.id).all())


def test_lote_nuevo_y_ajuste_a_mano(auth_headers, test_product_batch, db_session,
                                    test_user_with_role_permissions_branch_auth):
    # el lote del fixture nace con 100 (sin petición: sin usuario)
    first = _movements(db_session, test_product_batch)
    assert [(m.delta, m.quantity_after, m.user_id) for m in first] == [(100, 100, None)]

    response = client.put(f"/api/v1/productsbatches/{test_product_batch.id}",
                          json={"quantity": 80}, headers=auth_headers)
    assert response.status_code == 200, response.text

    last = _movements(db_session, test_product_batch)[-1]
    assert (last.delta, last.quantity_after) == (-20, 80)
    assert last.user_id == test_user_with_role_permissions_branch_auth.id
    assert last.source == f"PUT /api/v1/productsbatches/{test_product_batch.id}"


def test_venta_deja_movimiento(auth_headers, test_branch, test_product,
                               test_product_batch, db_session):
    response = client.post("/api/v1/sales/checkout", headers=auth_headers, json={
        "branch_id": test_branch.id,
        "items": [{"product_id": test_product.id, "quantity": "3"}],
    })
    assert response.status_code == 201, response.text

    last = _movements(db_session, test_product_batch)[-1]
    assert (last.delta, last.quantity_after, last.source) == (-3, 97, "POST /api/v1/sales/checkout")


def test_cambiar_otro_campo_no_deja_movimiento(auth_headers, test_product_batch, db_session):
    client.put(f"/api/v1/productsbatches/{test_product_batch.id}",
               json={"purchase_price": 9.5}, headers=auth_headers)
    assert len(_movements(db_session, test_product_batch)) == 1
