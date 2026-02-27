"""
possystem/seeds/seed_products_alimentos.py
"""
from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.seeds.helpers.seeder_helpers import (
    get_or_create_brand,
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Alimentos y bebidas"

GOLOSINAS = [
    {"sku": "009800120802", "title": "Ferrero Rocher C/8 Bolsa", "brand": "Ferrero", "cost": 95},
    {"sku": "009800190096", "title": "Ferrero Rondnoir", "brand": "Ferrero", "cost": 95},
    {"sku": "7501056008215", "title": "Clorets", "brand": "Clorets", "cost": 18},
    {"sku": "7501058638083", "title": "Carlos V", "brand": "Carlos V", "cost": 11},
    {"sku": "7501059281165", "title": "Frescas", "brand": "Frescas", "cost": 18},
    {"sku": "7501059299429", "title": "Larin Rojo", "brand": "Larin", "cost": 16},
    {"sku": "7501059299436", "title": "Larin Verde", "brand": "Larin", "cost": 16},
    {"sku": "7501059299443", "title": "Larin Azul", "brand": "Larin", "cost": 16},
    {"sku": "7501125103582", "title": "Electrolit Piña", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125104268", "title": "Electrolit Fresa", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125104343", "title": "Electrolit Manzana", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125104411", "title": "Electrolit Coco", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125104688", "title": "Electrolit Naranja Mandarina", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125118562", "title": "Electrolit Lima Limón", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125144851", "title": "Electrolit Uva", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125149221", "title": "Electrolit Fresa Kiwi", "brand": "Electrolit", "cost": 25},
    {"sku": "7501125174797", "title": "Electrolit Mora", "brand": "Electrolit", "cost": 25},
    {"sku": "7502271911427", "title": "M&M Chocolate", "brand": "M&M's", "cost": 18},
    {"sku": "7502271911472", "title": "M&M Cacahuate", "brand": "M&M's", "cost": 18},
    {"sku": "7502271916248", "title": "Turin Especial", "brand": "Turin", "cost": 145},
    {"sku": "7506174512200", "title": "Milky Way", "brand": "Mars", "cost": 20},
    {"sku": "7506174512248", "title": "Snickers", "brand": "Mars", "cost": 18},
    {"sku": "758104000159", "title": "Agua Bonafont 1.5L", "brand": "Bonafont", "cost": 15},
    {"sku": "758104001712", "title": "Agua Bonafont 600ml", "brand": "Bonafont", "cost": 8},
    {"sku": "758104100422", "title": "Agua Bonafont 1L", "brand": "Bonafont", "cost": 12},
]


def _classify(title: str) -> str:
    t = title.lower()
    if "electrolit" in t or "agua" in t:
        return "Bebidas"
    if "paleta" in t:
        return "Paletas"
    if any(x in t for x in ["ferrero", "snickers", "milky", "m&m", "turin"]):
        return "Chocolates"
    if any(x in t for x in ["clorets", "halls", "trident", "frescas", "larin"]):
        return "Caramelos y chicles"
    return "Otros dulces"


def seed_golosinas(db: Session):
    created = skipped = 0

    for item in GOLOSINAS:
        subcat = _classify(item["title"])
        category_id = get_or_create_category(db, subcat, ROOT)
        brand_id = get_or_create_brand(db, item["brand"])

        cost = float(item["cost"])
        _, was_created = get_or_create_product(
            db,
            title=item["title"],
            sku=item["sku"],
            brand_id=brand_id,
            category_id=category_id,
            price_cost=cost,
            price_retail=round(cost * 1.40, 2),
            description="Producto de golosina precargado",
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Golosinas insertadas:   {created}")
    print(f"⚠️  Duplicados omitidos:    {skipped}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_golosinas(db)
    finally:
        db.close()