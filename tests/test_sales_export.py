"""Excel de ventas de un periodo: todas las ventas, con sus productos."""
from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi import status
from openpyxl import load_workbook

from .test_convention_extras import _checkout, _mixed, _today
from .utils import client

EXPORT = "/api/v1/sales/export"


def _book(headers, **params):
    res = client.get(EXPORT, params=params, headers=headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert "spreadsheetml" in res.headers["content-type"]
    return load_workbook(BytesIO(res.content))


def _rows(sheet):
    """Filas como dict, a partir de los encabezados (fila 1)."""
    head, *rows = sheet.iter_rows(values_only=True)
    return [dict(zip(head, row)) for row in rows]


def test_export_trae_ventas_productos_y_resumen(auth_headers, test_branch, test_product_category,
                                                db_session):
    _, mine, theirs = _mixed(auth_headers, test_product_category.id, db_session)
    sale = _checkout(auth_headers, test_branch, [(mine["id"], 2), (theirs["id"], 1)])
    cancelled = _checkout(auth_headers, test_branch, [(theirs["id"], 1)])
    assert client.post(f"/api/v1/sales/{cancelled['id']}/cancel",
                       headers=auth_headers).status_code == 200
    old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    _checkout(auth_headers, test_branch, [(mine["id"], 1)], sold_at=old)

    book = _book(auth_headers, date_from=_today(), date_to=_today())
    assert book.sheetnames == ["Resumen", "Ventas", "Productos vendidos"]

    sales = {r["# Venta"]: r for r in _rows(book["Ventas"])}
    assert set(sales) == {sale["id"], cancelled["id"]}  # la de hace 3 días no
    row = sales[sale["id"]]
    assert row["Estado"] == "Completada" and row["Total"] == 460
    assert row["Productos"] == f"2× {mine['title']}\n1× {theirs['title']}"
    assert row["Efectivo"] == 1
    assert sales[cancelled["id"]]["Estado"] == "Cancelada"

    lines = [r for r in _rows(book["Productos vendidos"]) if r["# Venta"] == sale["id"]]
    assert [(r["Producto"], r["De quién es"], r["Cantidad"], r["Precio"], r["Importe"])
            for r in lines] == [(mine["title"], "Propio", 2, 80, 160),
                                (theirs["title"], "Insectario Vecino", 1, 300, 300)]

    # el resumen solo suma lo completado, como el corte de caja
    summary = {r[0]: r[1:] for r in book["Resumen"].iter_rows(values_only=True) if r[0]}
    assert summary["Ventas completadas"][0] == 1
    assert summary["Total vendido"][0] == 460
    assert summary["Propio"][:2] == (2, 160)
    assert summary["Insectario Vecino"][:2] == (1, 300)


def test_export_no_se_corta_en_una_pagina_y_filtra_por_estado(
        auth_headers, test_branch, test_product_category, db_session):
    _, mine, _ = _mixed(auth_headers, test_product_category.id, db_session)
    for _ in range(12):
        _checkout(auth_headers, test_branch, [(mine["id"], 1)])
    assert len(_rows(_book(auth_headers)["Ventas"])) == 12
    assert _rows(_book(auth_headers, status_filter="cancelled")["Ventas"]) == []


def test_export_dia_y_hora_de_mexico(auth_headers, test_branch, test_product_category, db_session):
    _, mine, _ = _mixed(auth_headers, test_product_category.id, db_session)
    # 8 pm del 21 en México = 02:00 del 22 en UTC
    _checkout(auth_headers, test_branch, [(mine["id"], 1)], sold_at="2026-09-22T02:00:00Z")
    row, = _rows(_book(auth_headers, date_from="2026-09-21", date_to="2026-09-21")["Ventas"])
    assert row["Fecha"].strftime("%Y-%m-%d") == "2026-09-21"
    assert row["Hora"].strftime("%H:%M") == "20:00"


def test_export_un_texto_con_igual_no_es_formula(auth_headers, test_branch, test_product_category,
                                                 db_session):
    from pharmatrack.models.products.orm import Product
    _, mine, _ = _mixed(auth_headers, test_product_category.id, db_session)
    db_session.query(Product).filter_by(id=mine["id"]).update({"title": "=1+1\x07"})
    db_session.commit()
    _checkout(auth_headers, test_branch, [(mine["id"], 1)])
    sheet = _book(auth_headers)["Productos vendidos"]
    cell, = [c for c in sheet[2] if c.value == "=1+1"]
    assert cell.data_type == "s"


def test_export_pide_sesion():
    assert client.get(EXPORT).status_code in (401, 403)
