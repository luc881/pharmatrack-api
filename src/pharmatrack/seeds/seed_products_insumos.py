"""
pharmatrack/seeds/seed_products_insumos.py

Insumos de la tienda de animales, visibles en el sitio público.

Todo cuelga de la raíz "Insumos para terrario": ese subárbol separa los
productos de la tienda de animales del catálogo de farmacia (personas),
así una categoría como "Suplementos" puede existir en ambos mundos sin
chocar. Los de granel se venden por peso (venta libre, se pesa y se
cobra por gramo); los de pieza también van sin control de lotes hasta
que se decida llevar stock.

Idempotente: corre siempre; crea lo que falte y re-aplica categoría y
visibilidad a los SKUs sembrados.
"""
from sqlalchemy.orm import Session

from pharmatrack.models.products.orm import Product
from pharmatrack.seeds.helpers.seeder_helpers import (
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Insumos para terrario"

# (sku, título, subcategoría, unidad, precio, costo, descripción)
INSUMOS = [
    # ── Sustratos ──
    ("CORTEZA-G", "Corteza de encino (granel)", "Sustratos", "g", 0.06, 0.02,
     "Corteza natural para terrario. Se pesa la pieza y se cobra por gramo."),
    ("FIBRA-COCO", "Fibra de coco prensada", "Sustratos", "pieza", 45, 20,
     "Ladrillo de fibra de coco: rinde ~8 L de sustrato hidratado."),
    ("HOJARASCA-G", "Hojarasca de encino (granel)", "Sustratos", "g", 0.05, 0.015,
     "Hojas secas para bioactivos: refugio y alimento de isópodos."),
    # ── Decoración ──
    ("PIEDRA-G", "Piedra decorativa (granel)", "Decoración", "g", 0.08, 0.03,
     "Piedra para paisajismo de terrario. Se pesa y se cobra por gramo."),
    ("MADERA-G", "Madera de resina (granel)", "Decoración", "g", 0.10, 0.04,
     "Troncos y ramas para trepar. Se pesa la pieza y se cobra por gramo."),
    ("PLANTA-ART", "Planta artificial mediana", "Decoración", "pieza", 60, 25,
     "Planta colgante de plástico suave, ideal para arborícolas."),
    # ── Musgo y plantas ──
    ("MUSGO-G", "Musgo sphagnum (granel)", "Musgo y plantas", "g", 0.15, 0.06,
     "Musgo para retención de humedad. Se pesa y se cobra por gramo."),
    # ── Escondites y accesorios ──
    ("CUEVA-RES", "Cueva de resina", "Escondites y accesorios", "pieza", 80, 35,
     "Escondite de resina con acabado de roca, fácil de lavar."),
    ("BEBEDERO-CH", "Bebedero chico", "Escondites y accesorios", "pieza", 35, 12,
     "Bebedero bajo de plástico rígido, tamaño ideal para tarántulas y geckos."),
]


def seed_insumos(db: Session):
    created = 0
    for sku, title, category, unit, price, cost, description in INSUMOS:
        category_id = get_or_create_category(db, category, parent_name=ROOT)
        product, was_created = get_or_create_product(
            db,
            title=title,
            sku=sku,
            brand_id=None,
            category_id=category_id,
            price_cost=cost,
            price_retail=price,
            description=description,
            unit_name=unit,
            is_unit_sale=unit != "g",
            tracks_batches=False,
            show_online=True,
        )
        created += int(was_created)
        # Re-aplicar categoría/visibilidad a filas sembradas con versiones previas
        if not was_created:
            db.query(Product).filter(Product.sku == sku).update(
                {Product.product_category_id: category_id, Product.show_online: True},
                synchronize_session=False,
            )
    db.commit()
    print(f"   Insumos de la tienda: {created} creados, {len(INSUMOS) - created} ya existían")
