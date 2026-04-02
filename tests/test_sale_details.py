from decimal import Decimal

from pharmatrack.api.routes.sale_details import get_db as original_get_db
from .utils import override_get_db, app, client, route_client_factory
from fastapi import status

app.dependency_overrides[original_get_db] = override_get_db
sd_get, sd_post, sd_put, sd_patch, sd_delete = route_client_factory(client, "saledetails")


# ==================================================================
# READ ALL  (paginado igual que sales)
# ==================================================================
def test_read_all_sale_details(auth_headers, test_sale_detail):
    response = sd_get("/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "data" in body
    data = body["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_sale_detail.id for item in data)


def test_read_all_sale_details_no_auth():
    response = sd_get("/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# CREATE
# ==================================================================
def test_create_sale_detail(auth_headers, test_sale, test_product, db_session):
    payload = {
        "sale_id": test_sale.id,
        "product_id": test_product.id,
        "quantity": 3,
        "discount": 5.0,
        "description": "Detalle de venta de producto A",
    }
    response = sd_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    quantity = 3
    price_unit = float(test_product.price_retail)
    discount = 5.0
    line_subtotal = (price_unit * quantity) - discount

    expected_tax = 0.0
    if test_product.tax_percentage:
        expected_tax = line_subtotal * float(test_product.tax_percentage) / 100

    expected_total = line_subtotal + expected_tax

    assert data["product_id"] == test_product.id
    assert float(data["quantity"]) == quantity
    assert float(data["price_unit"]) == price_unit
    assert float(data["discount"]) == discount
    assert float(data["tax"]) == expected_tax
    assert float(data["total"]) == expected_total

    # La venta se recalculó
    db_session.refresh(test_sale)
    assert float(test_sale.subtotal) == line_subtotal
    assert float(test_sale.tax) == expected_tax
    assert float(test_sale.total) == expected_total


def test_create_sale_detail_invalid_sale(auth_headers, test_product):
    payload = {
        "sale_id": 9999,
        "product_id": test_product.id,
        "quantity": 2,
    }
    response = sd_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated sale not found"


def test_create_sale_detail_invalid_product(auth_headers, test_sale):
    payload = {
        "sale_id": test_sale.id,
        "product_id": 9999,
        "quantity": 2,
    }
    response = sd_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated product not found"


def test_create_sale_detail_non_draft_sale(auth_headers, completed_sale, test_product):
    payload = {
        "sale_id": completed_sale.id,
        "product_id": test_product.id,
        "quantity": 1,
    }
    response = sd_post("/", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cannot add details to a non-draft sale"


def test_create_sale_detail_no_auth(test_sale, test_product):
    payload = {
        "sale_id": test_sale.id,
        "product_id": test_product.id,
        "quantity": 1,
    }
    response = sd_post("/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# UPDATE
# ==================================================================
def test_update_sale_detail_recalculates_totals(
    auth_headers, test_sale_detail, another_product, db_session
):
    payload = {
        "product_id": another_product.id,
        "quantity": 5,
        "discount": 10.0,
        "description": "Detalle actualizado",
    }
    response = sd_put(f"/{test_sale_detail.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    price_unit = float(another_product.price_retail)
    line_subtotal = (price_unit * 5) - 10.0

    expected_tax = 0.0
    if another_product.tax_percentage:
        expected_tax = line_subtotal * float(another_product.tax_percentage) / 100

    expected_total = line_subtotal + expected_tax

    assert data["product_id"] == another_product.id
    assert float(data["quantity"]) == 5
    assert float(data["price_unit"]) == price_unit
    assert float(data["discount"]) == 10.0
    assert float(data["tax"]) == expected_tax
    assert float(data["total"]) == expected_total
    assert data["description"] == "Detalle actualizado"

    sale = test_sale_detail.sale
    db_session.refresh(sale)
    assert float(sale.subtotal) == line_subtotal
    assert float(sale.tax) == expected_tax
    assert float(sale.total) == expected_total


def test_update_sale_detail_change_product_and_recalculate(
    auth_headers, test_sale_detail, another_product, db_session
):
    payload = {
        "product_id": another_product.id,
        "quantity": 4,
        "discount": 20.0,
        "description": "Producto cambiado y recalculado",
    }
    response = sd_put(f"/{test_sale_detail.id}", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    price_unit = float(another_product.price_retail)
    line_subtotal = (price_unit * 4) - 20.0

    expected_tax = 0.0
    if another_product.tax_percentage:
        expected_tax = line_subtotal * float(another_product.tax_percentage) / 100

    expected_total = line_subtotal + expected_tax

    assert data["product_id"] == another_product.id
    assert float(data["quantity"]) == 4
    assert float(data["price_unit"]) == price_unit
    assert float(data["discount"]) == 20.0
    assert float(data["tax"]) == expected_tax
    assert float(data["total"]) == expected_total

    sale = test_sale_detail.sale
    db_session.refresh(sale)
    assert float(sale.subtotal) == line_subtotal
    assert float(sale.tax) == expected_tax
    assert float(sale.total) == expected_total


def test_update_sale_detail_not_found(auth_headers):
    response = sd_put("/9999", json={"quantity": 5}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale detail not found"


def test_update_sale_detail_non_draft_sale(auth_headers, sale_detail_completed_sale):
    response = sd_put(
        f"/{sale_detail_completed_sale.id}",
        json={"quantity": 10},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cannot modify details of a non-draft sale"


def test_update_sale_detail_invalid_product(auth_headers, test_sale_detail):
    response = sd_put(
        f"/{test_sale_detail.id}",
        json={"product_id": 9999},
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Associated product not found"


def test_update_sale_detail_no_auth(test_sale_detail):
    response = sd_put(f"/{test_sale_detail.id}", json={"quantity": 1})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==================================================================
# DELETE
# ==================================================================
def test_delete_sale_detail_recalculates_sale(
    auth_headers, test_sale_detail, db_session
):
    sale = test_sale_detail.sale
    initial_subtotal = float(sale.subtotal)
    initial_tax = float(sale.tax)
    initial_total = float(sale.total)

    response = sd_delete(f"/{test_sale_detail.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # El detalle ya no existe
    from pharmatrack.models.sale_details.orm import SaleDetail
    assert db_session.get(SaleDetail, test_sale_detail.id) is None

    # La venta se recalculó (totales bajaron)
    db_session.refresh(sale)
    assert float(sale.subtotal) < initial_subtotal
    assert float(sale.tax) <= initial_tax
    assert float(sale.total) < initial_total


def test_delete_sale_detail_non_draft_sale(auth_headers, sale_detail_completed_sale):
    response = sd_delete(f"/{sale_detail_completed_sale.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Cannot delete details of a non-draft sale"


def test_delete_sale_detail_not_found(auth_headers):
    response = sd_delete("/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sale detail not found"


def test_delete_sale_detail_no_auth(test_sale_detail):
    response = sd_delete(f"/{test_sale_detail.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED