"""Convención: productos provisionales, «se prepara», dueño y corte por dueño."""
from datetime import datetime, timedelta, timezone

from fastapi import status

from .utils import client
from .test_bundles import _make_product, _add_batch

CATALOG = "/api/v1/products/quick-sale"
PROVISIONAL = "/api/v1/products/provisional"
CHECKOUT = "/api/v1/sales/checkout"
CUT = "/api/v1/sales/report/by-owner"
CDMX = timezone(timedelta(hours=-6))


def _supplier(db_session, name="Insectario Vecino"):
    from pharmatrack.models.suppliers.orm import Supplier

    supplier = Supplier(name=name)
    db_session.add(supplier)
    db_session.commit()
    return supplier.id


def _provisional(auth_headers, key="equipo-a-0001", **extra):
    body = {"client_key": key, "title": "Tronco de corcho", "price_retail": 120, **extra}
    return client.post(PROVISIONAL, json=body, headers=auth_headers)


def _checkout(auth_headers, branch, lines, **extra):
    res = client.post(CHECKOUT, headers=auth_headers, json={
        "branch_id": branch.id,
        "items": [{"product_id": pid, "quantity": str(qty)} for pid, qty in lines],
        "payments": [{"method_payment": "cash", "amount": "1.00"}],
        **extra,
    })
    assert res.status_code == status.HTTP_201_CREATED, res.text
    return res.json()


def _today():
    return datetime.now(CDMX).date().isoformat()


# =========================================================
# Campos nuevos del producto
# =========================================================
def test_product_new_fields_default_and_update(auth_headers, test_product_category, db_session):
    product = _make_product(auth_headers, test_product_category.id, sku="N1")
    assert product["needs_prep"] is False
    assert product["consignor_id"] is None
    assert product["provisional"] is False

    owner = _supplier(db_session)
    res = client.put(f"/api/v1/products/{product['id']}", headers=auth_headers,
                     json={"needs_prep": True, "consignor_id": owner})
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["needs_prep"] is True
    assert res.json()["consignor_id"] == owner

    res = client.put(f"/api/v1/products/{product['id']}", headers=auth_headers,
                     json={"consignor_id": 999999})
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    # null = vuelve a ser propio
    res = client.put(f"/api/v1/products/{product['id']}", headers=auth_headers,
                     json={"consignor_id": None})
    assert res.json()["consignor_id"] is None


def test_quick_sale_catalog_includes_new_fields(auth_headers, test_product_category, db_session):
    owner = _supplier(db_session)
    _make_product(auth_headers, test_product_category.id, sku="S1", quick_sale=True,
                  needs_prep=True, consignor_id=owner)
    item = client.get(CATALOG, headers=auth_headers).json()[0]
    assert item["needs_prep"] is True
    assert item["consignor_id"] == owner
    assert item["provisional"] is False and item["client_key"] is None


def test_list_filters_by_provisional(auth_headers, test_product_category):
    _make_product(auth_headers, test_product_category.id, sku="F1")
    _provisional(auth_headers)
    res = client.get("/api/v1/products?provisional=true", headers=auth_headers).json()
    assert [p["title"].lower() for p in res["data"]] == ["tronco de corcho"]


# =========================================================
# Alta de provisional
# =========================================================
def test_provisional_create_and_sell(auth_headers, test_branch, db_session):
    owner = _supplier(db_session)
    res = _provisional(auth_headers, needs_prep=True, consignor_id=owner)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    item = res.json()
    assert item["provisional"] is True and item["client_key"] == "equipo-a-0001"
    assert item["stock"] is None  # sin control de existencias
    assert item["needs_prep"] is True and item["consignor_id"] == owner
    assert item["category"] == "De último momento"

    catalog = client.get(CATALOG, headers=auth_headers).json()
    assert [i["id"] for i in catalog] == [item["id"]]

    sale = _checkout(auth_headers, test_branch, [(item["id"], 2)])
    assert float(sale["total"]) == 240


def test_provisional_is_idempotent(auth_headers):
    first = _provisional(auth_headers).json()
    again = _provisional(auth_headers, title="Otro nombre", price_retail=5)
    assert again.status_code == status.HTTP_201_CREATED
    assert again.json()["id"] == first["id"]
    assert again.json()["title"] == first["title"]


def test_provisional_same_title_two_devices(auth_headers):
    a = _provisional(auth_headers, key="equipo-a-0001")
    b = _provisional(auth_headers, key="equipo-b-0001")
    assert a.status_code == b.status_code == status.HTTP_201_CREATED
    assert a.json()["id"] != b.json()["id"]


def test_provisional_bad_consignor(auth_headers):
    assert _provisional(auth_headers, consignor_id=999999).status_code == status.HTTP_400_BAD_REQUEST


def test_provisional_validates_body(auth_headers):
    assert _provisional(auth_headers, price_retail=0).status_code == 422
    assert _provisional(auth_headers, title=" ").status_code == 422


def test_provisional_requires_login():
    res = client.post(PROVISIONAL, json={"client_key": "equipo-a-0001", "title": "X",
                                         "price_retail": 1})
    assert res.status_code in (401, 403)


# =========================================================
# Revisión de provisionales
# =========================================================
def test_provisional_review_lists_sold_units(auth_headers, test_branch):
    item = _provisional(auth_headers).json()
    _provisional(auth_headers, key="equipo-a-0002", title="Sin ventas")
    _checkout(auth_headers, test_branch, [(item["id"], 2)])
    _checkout(auth_headers, test_branch, [(item["id"], 1)])

    res = client.get(PROVISIONAL, headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    rows = {r["title"]: r for r in res.json()}
    assert rows["Tronco de corcho"]["units_sold"] == 3
    assert float(rows["Tronco de corcho"]["amount"]) == 360
    assert rows["Sin ventas"]["units_sold"] == 0

    # conservar: deja de ser provisional y sale de la lista
    res = client.put(f"/api/v1/products/{item['id']}", headers=auth_headers,
                     json={"provisional": False})
    assert res.status_code == status.HTTP_200_OK, res.text
    assert [r["title"] for r in client.get(PROVISIONAL, headers=auth_headers).json()] == ["Sin ventas"]


def test_discarded_provisional_leaves_the_quick_sale(auth_headers):
    item = _provisional(auth_headers).json()
    res = client.put(f"/api/v1/products/{item['id']}", headers=auth_headers,
                     json={"is_active": False, "quick_sale": False})
    assert res.status_code == status.HTTP_200_OK, res.text
    assert client.get(CATALOG, headers=auth_headers).json() == []
    assert client.get(PROVISIONAL, headers=auth_headers).json()[0]["is_active"] is False


# =========================================================
# Corte por dueño
# =========================================================
def _mixed(auth_headers, category_id, db_session):
    owner = _supplier(db_session)
    mine = _make_product(auth_headers, category_id, sku="M1", title="Cueva", price_retail=80)
    theirs = _make_product(auth_headers, category_id, sku="T1", title="Mantis",
                           price_retail=300, consignor_id=owner)
    for p in (mine, theirs):
        _add_batch(db_session, p["id"], 20)
    return owner, mine, theirs


def test_owner_cut_splits_mixed_ticket(auth_headers, test_branch, test_product_category, db_session):
    owner, mine, theirs = _mixed(auth_headers, test_product_category.id, db_session)
    sale = _checkout(auth_headers, test_branch, [(mine["id"], 2), (theirs["id"], 1)])

    res = client.get(CUT, params={"date_from": _today(), "date_to": _today()}, headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    cut = res.json()
    assert [c["owner"] for c in cut] == ["Propio", "Insectario Vecino"]
    assert cut[0]["consignor_id"] is None and cut[1]["consignor_id"] == owner
    assert float(cut[0]["amount"]) == 160 and cut[0]["units"] == 2
    assert float(cut[1]["amount"]) == 300 and cut[1]["units"] == 1
    assert cut[1]["products"] == [
        {"product_id": theirs["id"], "title": "Mantis", "units": 1, "amount": "300.00"}
    ]
    assert sum(float(c["amount"]) for c in cut) == float(sale["total"])


def test_owner_cut_ignores_cancelled_and_other_dates(auth_headers, test_branch,
                                                     test_product_category, db_session):
    from pharmatrack.models.sales.orm import Sale

    _, mine, theirs = _mixed(auth_headers, test_product_category.id, db_session)
    cancelled = _checkout(auth_headers, test_branch, [(theirs["id"], 1)])
    db_session.query(Sale).filter_by(id=cancelled["id"]).update({"status": "cancelled"})
    db_session.commit()
    old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    _checkout(auth_headers, test_branch, [(mine["id"], 1)], sold_at=old)
    _checkout(auth_headers, test_branch, [(mine["id"], 1)])

    cut = client.get(CUT, params={"date_from": _today(), "date_to": _today()},
                     headers=auth_headers).json()
    assert [(c["owner"], float(c["amount"])) for c in cut] == [("Propio", 80.0)]


def test_owner_cut_requires_login():
    assert client.get(CUT, params={"date_from": "2026-11-22", "date_to": "2026-11-22"}).status_code in (401, 403)
