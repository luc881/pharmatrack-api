"""Excel de ventas: resumen, una fila por venta y una fila por producto vendido."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from pharmatrack.types.sales import PaymentMethodEnum, SaleStatusEnum
from pharmatrack.utils.mx_day import MX_OFFSET

STATUS_LABEL = {
    SaleStatusEnum.DRAFT: "Borrador",
    SaleStatusEnum.COMPLETED: "Completada",
    SaleStatusEnum.CANCELLED: "Cancelada",
    SaleStatusEnum.REFUNDED: "Reembolsada",
    SaleStatusEnum.PARTIALLY_REFUNDED: "Reemb. parcial",
}
METHODS = [
    (PaymentMethodEnum.CASH, "Efectivo"),
    (PaymentMethodEnum.CARD, "Tarjeta"),
    (PaymentMethodEnum.TRANSFER, "Transferencia"),
]

MONEY = '"$"#,##0.00'
FORMATS = {"Fecha": "dd/mm/yyyy", "Hora": "hh:mm"}
MONEY_COLUMNS = {"Precio", "Descuento", "Importe", "Subtotal", "Impuesto", "Total",
                 "Efectivo", "Tarjeta", "Transferencia"}
WRAP_COLUMNS = {"Productos", "Producto", "Observaciones"}
HEAD_FILL = PatternFill("solid", fgColor="2F4A3A")
HEAD_FONT = Font(bold=True, color="FFFFFF")
MUTED = Font(color="999999")

# columna → ancho
SALE_COLUMNS = {
    "# Venta": 9, "Fecha": 12, "Hora": 8, "Estado": 15, "Productos": 48, "Subtotal": 12,
    "Descuento": 12, "Impuesto": 11, "Total": 12, "Efectivo": 12, "Tarjeta": 12,
    "Transferencia": 14, "Sucursal": 20, "Cobró": 22, "Observaciones": 40,
}
LINE_COLUMNS = {
    "# Venta": 9, "Fecha": 12, "Hora": 8, "Estado": 15, "Producto": 44, "SKU": 16,
    "De quién es": 20, "Cantidad": 10, "Precio": 12, "Descuento": 12, "Impuesto": 11,
    "Importe": 12, "Pago": 22, "Cobró": 22,
}


def _put(sheet, row, column, value):
    cell = sheet.cell(row=row, column=column)
    if isinstance(value, str):
        cell.value = ILLEGAL_CHARACTERS_RE.sub("", value)
        cell.data_type = "s"  # un título que empieza con «=» no es una fórmula
    else:
        cell.value = value
    return cell


def _head(sheet, row, values):
    for i, value in enumerate(values, start=1):
        cell = _put(sheet, row, i, value)
        cell.font, cell.fill = HEAD_FONT, HEAD_FILL


def _table(sheet, columns, rows):
    """rows: [(fila como dict, ¿en gris?)]. Encabezado fijo y con filtros."""
    _head(sheet, 1, columns)
    for i, width in enumerate(columns.values(), start=1):
        sheet.column_dimensions[get_column_letter(i)].width = width
    for r, (row, muted) in enumerate(rows, start=2):
        for i, name in enumerate(columns, start=1):
            cell = _put(sheet, r, i, row[name])
            cell.alignment = Alignment(vertical="top", wrap_text=name in WRAP_COLUMNS)
            if name in MONEY_COLUMNS:
                cell.number_format = MONEY
            elif name in FORMATS:
                cell.number_format = FORMATS[name]
            if muted:
                cell.font = MUTED
        # Excel no siempre ajusta solo el alto de una celda de varias líneas
        lines = row.get("Productos", "").count("\n") + 1
        if lines > 1:
            sheet.row_dimensions[r].height = min(15 * lines, 400)  # Excel no pasa de 409
    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_LETTER
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.print_title_rows = "1:1"


def _summary(sheet, sales, owner_of, period):
    """Solo suma lo completado, igual que el corte de caja."""
    done = [s for s in sales if s.status == SaleStatusEnum.COMPLETED]
    row = 1

    def put(*values, bold=False, money=None):
        nonlocal row
        for i, value in enumerate(values, start=1):
            cell = _put(sheet, row, i, value)
            cell.font = Font(bold=bold)
            if i == money:
                cell.number_format = MONEY
        row += 1

    def heading(*values):
        nonlocal row
        _head(sheet, row + 1, values)
        row += 2

    put("Ventas", bold=True)
    sheet["A1"].font = Font(bold=True, size=16)
    put("Periodo", period)
    put("Ventas completadas", len(done))
    put("Total vendido", sum(s.total for s in done), bold=True, money=2)
    if len(done) < len(sales):
        put("Canceladas, reembolsadas o en borrador (no suman)", len(sales) - len(done))

    heading("Forma de pago", "Importe")
    for method, label in METHODS:
        put(label, sum(p.amount for s in done for p in s.sale_payments
                       if p.method_payment == method), money=2)

    owners: dict = {}  # consignor_id → {product_id: [título, piezas, importe]}
    for line in (d for s in done for d in s.sale_details):
        entry = owners.setdefault(line.product.consignor_id, {}).setdefault(
            line.product_id, [line.product.title, 0, 0])
        entry[1] += float(line.quantity)
        entry[2] += line.total
    # Propio primero; después por nombre
    for owner_id in sorted(owners, key=lambda o: (o is not None, owner_of(o).lower())):
        products = owners[owner_id].values()
        heading("Por dueño", "Cantidad", "Importe")
        put(owner_of(owner_id), sum(p[1] for p in products), sum(p[2] for p in products),
            bold=True, money=3)
        for title, units, amount in sorted(products, key=lambda p: -p[2]):
            put(f"   {title}", units, amount, money=3)

    for column, width in (("A", 52), ("B", 28), ("C", 16)):
        sheet.column_dimensions[column].width = width
    for cell in sheet["B"]:
        cell.alignment = Alignment(horizontal="right")
    sheet.page_setup.paperSize = sheet.PAPERSIZE_LETTER
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True


def sales_workbook(sales, owner_names: dict, period: str) -> bytes:
    def owner_of(consignor_id):
        return owner_names.get(consignor_id, "Propio")

    sale_rows, line_rows = [], []
    for sale in sales:
        when = sale.date_sale - MX_OFFSET
        muted = sale.status != SaleStatusEnum.COMPLETED
        paid = {label: sum(p.amount for p in sale.sale_payments if p.method_payment == method)
                for method, label in METHODS}
        details = sorted(sale.sale_details, key=lambda d: d.id)
        base = {
            "# Venta": sale.id,
            "Fecha": when.date(),
            "Hora": when.time().replace(second=0, microsecond=0),
            "Estado": STATUS_LABEL[sale.status],
            "Cobró": " ".join(filter(None, [sale.user.name, sale.user.surname])),
        }
        sale_rows.append(({
            **base,
            "Productos": "\n".join(f"{float(d.quantity):g}× {d.product.title}" for d in details),
            "Subtotal": sale.subtotal,
            "Descuento": sale.discount,
            "Impuesto": sale.tax,
            "Total": sale.total,
            **{label: amount or None for label, amount in paid.items()},
            "Sucursal": sale.branch.name,
            "Observaciones": sale.description,
        }, muted))
        line_rows += [({
            **base,
            "Producto": d.product.title,
            "SKU": d.product.sku,
            "De quién es": owner_of(d.product.consignor_id),
            "Cantidad": float(d.quantity),
            "Precio": d.price_unit,
            "Descuento": d.discount,
            "Impuesto": d.tax,
            "Importe": d.total,
            "Pago": ", ".join(label for label, amount in paid.items() if amount),
        }, muted) for d in details]

    book = Workbook()
    book.active.title = "Resumen"
    _summary(book.active, sales, owner_of, period)
    _table(book.create_sheet("Ventas"), SALE_COLUMNS, sale_rows)
    _table(book.create_sheet("Productos vendidos"), LINE_COLUMNS, line_rows)

    out = BytesIO()
    book.save(out)
    return out.getvalue()
