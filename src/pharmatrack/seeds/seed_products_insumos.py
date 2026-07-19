"""
pharmatrack/seeds/seed_products_insumos.py

Insumos para terrario que se venden a granel por peso (venta libre):
la caja no lleva inventario — se pesa la pieza elegida y se cobra por
gramo. tracks_batches=False: la venta no valida ni descuenta lotes.

Idempotente por SKU: corre siempre, aunque el catálogo ya esté poblado.
"""
from sqlalchemy.orm import Session

from pharmatrack.seeds.helpers.seeder_helpers import (
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Insumos para terrario"

# (sku, título, categoría, precio por gramo, costo por gramo, descripción)
GRANEL = [
    ("CORTEZA-G", "Corteza de encino (granel)", "Sustratos y decoración", 0.06, 0.02,
     "Corteza natural para terrario. Se pesa la pieza y se cobra por gramo."),
    ("PIEDRA-G", "Piedra decorativa (granel)", "Sustratos y decoración", 0.08, 0.03,
     "Piedra para paisajismo de terrario. Se pesa y se cobra por gramo."),
    ("MUSGO-G", "Musgo sphagnum (granel)", "Sustratos y decoración", 0.15, 0.06,
     "Musgo para retención de humedad. Se pesa y se cobra por gramo."),
    ("MADERA-G", "Madera de resina (granel)", "Sustratos y decoración", 0.10, 0.04,
     "Troncos y ramas para trepar. Se pesa la pieza y se cobra por gramo."),
]


def seed_insumos(db: Session):
    created = 0
    for sku, title, category, price_g, cost_g, description in GRANEL:
        category_id = get_or_create_category(db, category, parent_name=ROOT)
        _, was_created = get_or_create_product(
            db,
            title=title,
            sku=sku,
            brand_id=None,
            category_id=category_id,
            price_cost=cost_g,
            price_retail=price_g,
            description=description,
            unit_name="g",
            is_unit_sale=False,
            tracks_batches=False,
        )
        created += int(was_created)
    db.commit()
    print(f"   Insumos a granel: {created} creados, {len(GRANEL) - created} ya existían")
