from fastapi import status

from pharmatrack.models.product_batch.orm import ProductBatch
from .utils import client, route_client_factory

purchase_get, purchase_post, purchase_put, _, purchase_delete = route_client_factory(client, "purchases")
detail_get = route_client_factory(client, "purchase-details")[0]


def _stock(db, product_id):
    db.expire_all()
    return {
        (b.lot_code, b.expiration_date and b.expiration_date.isoformat()): b.quantity
        for b in db.query(ProductBatch).filter(ProductBatch.product_id == product_id)
    }


def _payload(supplier, user, items):
    return {
        "supplier_id": supplier.id,
        "user_id": user.id,
        "total": 100,
        "date_emision": "2026-10-01T00:00:00",
        "items": items,
    }


def test_purchase_adds_edits_and_removes_stock(
    auth_headers, db_session, test_supplier, test_user_with_role_permissions_branch_auth, test_product
):
    user = test_user_with_role_permissions_branch_auth
    pid = test_product.id
    items = [
        {"product_id": pid, "quantity": 10, "unit_price": 5, "lot_code": "L1", "expiration_date": "2030-01-01"},
        {"product_id": pid, "quantity": 4, "unit_price": 5},
    ]

    r = purchase_post("/", json=_payload(test_supplier, user, items), headers=auth_headers)
    assert r.status_code == status.HTTP_201_CREATED, r.text
    purchase_id = r.json()["id"]
    assert r.json()["date_emision"].startswith("2026-10-01")
    assert _stock(db_session, pid) == {("L1", "2030-01-01"): 10, (None, None): 4}

    # el listado de renglones filtra por compra
    rows = detail_get(params={"purchase_id": purchase_id}, headers=auth_headers).json()["data"]
    assert [d["quantity"] for d in rows] == [10, 4]
    assert detail_get(params={"purchase_id": 999999}, headers=auth_headers).json()["data"] == []

    # editar: resta lo viejo y suma lo nuevo
    r = purchase_put(
        f"/{purchase_id}",
        json={"items": [{"product_id": pid, "quantity": 3, "unit_price": 6, "lot_code": "L1", "expiration_date": "2030-01-01"}]},
        headers=auth_headers,
    )
    assert r.status_code == status.HTTP_200_OK, r.text
    assert _stock(db_session, pid) == {("L1", "2030-01-01"): 3}

    # si ya se vendió, no deja borrarla
    batch = db_session.query(ProductBatch).filter_by(product_id=pid, lot_code="L1").one()
    batch.quantity = 1
    db_session.commit()
    r = purchase_delete(f"/{purchase_id}", headers=auth_headers)
    assert r.status_code == status.HTTP_409_CONFLICT
    assert "Ya se vendió" in r.json()["detail"]

    batch.quantity = 3
    db_session.commit()
    assert purchase_delete(f"/{purchase_id}", headers=auth_headers).status_code == status.HTTP_204_NO_CONTENT
    assert _stock(db_session, pid) == {}


def test_purchase_rejects_fractional_quantity_for_stocked_product(
    auth_headers, test_supplier, test_user_with_role_permissions_branch_auth, test_product
):
    items = [{"product_id": test_product.id, "quantity": 1.5, "unit_price": 5}]
    r = purchase_post(
        "/", json=_payload(test_supplier, test_user_with_role_permissions_branch_auth, items), headers=auth_headers
    )
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "entera" in r.json()["detail"]
