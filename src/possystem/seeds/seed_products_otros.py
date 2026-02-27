"""
possystem/seeds/seed_products_otros.py
"""
from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.seeds.helpers.seeder_helpers import (
    get_or_create_brand,
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Miscelánea y hogar"

OTROS_PRODUCTOS = [
    {"sku": "039800011626", "title": "Eveready 9V C/1", "brand": "Eveready", "cost": 85},
    {"sku": "041333000985", "title": "Duracell D2 C/2", "brand": "Duracell", "cost": 135},
    {"sku": "041333001043", "title": "Duracell 9V", "brand": "Duracell", "cost": 135},
    {"sku": "041333012452", "title": "Duracell C14", "brand": "Duracell", "cost": 45},
    {"sku": "041333428482", "title": "Duracell AAA C/1", "brand": "Duracell", "cost": 25},
    {"sku": "041333666426", "title": "Duracell AA C/1", "brand": "Duracell", "cost": 25},
    {"sku": "7501037600056", "title": "Eveready AA C/4", "brand": "Eveready", "cost": 65},
    {"sku": "7501086107087", "title": "Encendedor", "brand": "Genérico", "cost": 10},
    {"sku": "7501102610003", "title": "Kolaloka Aplicador de precisión", "brand": "Kolaloka", "cost": 30},
    {"sku": "7501102614001", "title": "Kolaloka Goterito", "brand": "Kolaloka", "cost": 35},
    {"sku": "7501102614322", "title": "Kolaloka Brocha", "brand": "Kolaloka", "cost": 35},
    {"sku": "7501943412200", "title": "Petalo Papel Higiénico C/4 Rollos", "brand": "Petalo", "cost": 38},
    {"sku": "7502210680070", "title": "Amoniaco 1L", "brand": "Genérico", "cost": 32},
    {"sku": "7502210680087", "title": "Amoniaco 500ml", "brand": "Genérico", "cost": 18},
    {"sku": "7502210680155", "title": "Amoniaco 1L", "brand": "Genérico", "cost": 32},
    {"sku": "7502210681534", "title": "Borax", "brand": "Genérico", "cost": 5},
    {"sku": "7503022640016", "title": "Bicarbonato de sodio", "brand": "Genérico", "cost": 12},
    {"sku": "7506313000094", "title": "Amoniaco 500ml", "brand": "Genérico", "cost": 18},
    {"sku": "7506425601769", "title": "Kleenex Caja C/60", "brand": "Kleenex", "cost": 18},
    {"sku": "7506425613168", "title": "Kleenex Caja C/90", "brand": "Kleenex", "cost": 45},
    {"sku": "7591005574007", "title": "Raidolitos", "brand": "Raid", "cost": 35},
    {"sku": "8999002604755", "title": "Eveready AAA C/2", "brand": "Eveready", "cost": 30},
    {"sku": "CLO", "title": "Pastillas de cloro", "brand": "Genérico", "cost": 25},
    {"sku": "PC", "title": "Pastillas de cloro C/4", "brand": "Genérico", "cost": 25},
    {"sku": "LG", "title": "Liga", "brand": "Genérico", "cost": 12},
    {"sku": "PH", "title": "Papel higiénico rollo", "brand": "Genérico", "cost": 10},
    {"sku": "SAN", "title": "Sanitas", "brand": "Genérico", "cost": 23},
    {"sku": "7501058752796", "title": "Lysol 475g", "brand": "Lysol", "cost": 0},
]


def _classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["duracell", "eveready", "pila", "9v", " aa", "aaa"]):
        return "Pilas y energía"
    if any(x in t for x in ["amoniaco", "borax", "bicarbonato", "lysol", "cloro", "raid"]):
        return "Limpieza y desinfección"
    if "liga" in t:
        return "Papelería y oficina"
    if any(x in t for x in ["kolaloka", "encendedor"]):
        return "Adhesivos y ferretería ligera"
    if any(x in t for x in ["papel", "kleenex", "sanitas"]):
        return "Higiene del hogar"
    return "Otros"


def seed_otros(db: Session):
    created = skipped = 0

    for item in OTROS_PRODUCTOS:
        subcat = _classify(item["title"])
        # "Otros" is a root category, not a child of ROOT
        parent = ROOT if subcat != "Otros" else None
        category_id = get_or_create_category(db, subcat, parent)
        brand_id = get_or_create_brand(db, item["brand"])

        cost = float(item["cost"])
        _, was_created = get_or_create_product(
            db,
            title=item["title"],
            sku=item["sku"],
            brand_id=brand_id,
            category_id=category_id,
            price_cost=cost,
            price_retail=round(cost * 1.40, 2) if cost > 0 else 0,
            description="Producto misceláneo precargado",
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Otros productos insertados: {created}")
    print(f"⚠️  Duplicados omitidos:        {skipped}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_otros(db)
    finally:
        db.close()