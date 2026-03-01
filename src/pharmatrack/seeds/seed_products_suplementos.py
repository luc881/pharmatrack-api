"""
pharmatrack/seeds/seed_products_suplementos.py
"""
from sqlalchemy.orm import Session
from pharmatrack.db.session import SessionLocal
from pharmatrack.seeds.data.suplementos_json import SUPLEMENTOS
from pharmatrack.seeds.helpers.seeder_helpers import (
    get_or_create_brand,
    get_or_create_category,
    get_or_create_master,
    get_or_create_product,
    safe_float,
)

ROOT = "Suplementos y nutrición"

_TITLE_TO_SUBCAT: dict[str, str] = {
    "vitamina": "Vitaminas",
    "multivitamínico": "Vitaminas",
    "calcio": "Minerales",
    "magnesio": "Minerales",
    "hierro": "Minerales",
    "omega": "Omega y lípidos",
    "dha": "Omega y lípidos",
    "colágeno": "Colágeno y belleza",
    "melatonina": "Salud del sueño",
    "fibra": "Salud digestiva",
    "probiótico": "Probióticos y prebióticos",
    "pediasure": "Nutrición infantil",
    "nan ": "Nutrición infantil",
    "ensure": "Nutrición especializada",
    "glucerna": "Nutrición especializada",
}


def _detect_subcat(item: dict) -> str:
    # Always coerce with `or ""` — value may exist in JSON but be null
    explicit = str(item.get("subcategory") or "").strip()
    if explicit:
        return explicit

    title = str(item.get("title") or "").lower()
    for key, subcat in _TITLE_TO_SUBCAT.items():
        if key in title:
            return subcat

    return "Vitaminas"  # safe default


def seed_suplementos(db: Session):
    created = skipped = ingredients_linked = 0

    for item in SUPLEMENTOS:
        subcat = _detect_subcat(item)
        category_id = get_or_create_category(db, subcat, ROOT)
        brand_id    = get_or_create_brand(db, item.get("brand"))
        master_id   = get_or_create_master(db, item.get("product_master"))

        cost   = safe_float(item.get("cost"))
        retail = round(cost * 1.45, 2)

        ingredients = item.get("ingredients") or []

        product, was_created = get_or_create_product(
            db,
            title=item["title"],
            sku=item["sku"],
            brand_id=brand_id,
            category_id=category_id,
            product_master_id=master_id,
            price_cost=cost,
            price_retail=retail,
            description=f"Suplemento: {item.get('product_master') or ''}",
            ingredients=ingredients,
        )

        if was_created:
            ingredients_linked += len(ingredients)
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Suplementos insertados:    {created}")
    print(f"⚠️  Duplicados omitidos:       {skipped}")
    print(f"🧪 Ingredientes vinculados:   {ingredients_linked}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_suplementos(db)
    finally:
        db.close()