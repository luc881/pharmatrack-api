from decimal import Decimal
from sqlalchemy.orm import Session
from ...models.sales.orm import Sale

def recalc_sale_totals(db: Session, sale: Sale) -> None:
    subtotal = Decimal("0")
    tax_total = Decimal("0")

    for detail in sale.sale_details:
        line_subtotal = (detail.price_unit * detail.quantity) - detail.discount
        detail.total = line_subtotal + detail.tax

        subtotal += line_subtotal
        tax_total += detail.tax

    sale.subtotal = subtotal
    sale.tax = tax_total
    sale.total = subtotal + tax_total
