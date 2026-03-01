"""
pharmatrack/seeds/seed_products_medicamentos.py
"""
from sqlalchemy.orm import Session
from pharmatrack.db.session import SessionLocal
from pharmatrack.seeds.data.medicamentos_json import MEDICAMENTOS
from pharmatrack.seeds.helpers.seeder_helpers import (
    get_or_create_brand,
    get_or_create_category,
    get_or_create_master,
    get_or_create_product,
    safe_float,
)

ROOT = "Medicamentos"

# Fallback subcategory mapping if item["category"] is missing
_MASTER_TO_SUBCAT: dict[str, str] = {
    "paracetamol": "Analgésicos",
    "ácido acetilsalicílico": "Analgésicos",
    "metamizol": "Analgésicos",
    "ketorolaco": "Analgésicos",
    "tramadol": "Analgésicos",
    "diclofenaco": "Antiinflamatorios",
    "ibuprofeno": "Antiinflamatorios",
    "meloxicam": "Antiinflamatorios",
    "amoxicilina": "Antibióticos",
    "cloranfenicol": "Antibióticos",
    "cefalexina": "Antibióticos",
    "ciprofloxacino": "Antibióticos",
    "claritromicina": "Antibióticos",
    "eritromicina": "Antibióticos",
    "gentamicina": "Antibióticos",
    "lincomicina": "Antibióticos",
    "ampicilina": "Antibióticos",
    "ceftriaxona": "Antibióticos",
    "azitromicina": "Antibióticos",
    "doxiciclina": "Antibióticos",
    "fosfomicina": "Antibióticos",
    "omeprazol": "Gastrointestinales",
    "pantoprazol": "Gastrointestinales",
    "loratadina": "Antialérgicos",
    "cetirizina": "Antialérgicos",
    "tobramicina": "Oftalmológicos",
    "hipromelosa": "Oftalmológicos",
}


def _detect_subcat(item: dict) -> str:
    # item.get() can return None if the key exists but has a null value in JSON
    # so we always coerce with `or ""` before calling .strip()
    explicit = str(item.get("category") or "").strip()
    if explicit:
        return explicit

    master = str(item.get("product_master") or "").lower()
    title  = str(item.get("title")          or "").lower()

    for key, subcat in _MASTER_TO_SUBCAT.items():
        if key in master or key in title:
            return subcat

    return "Analgésicos"  # safe default


def seed_medicamentos(db: Session):
    created = skipped = ingredients_linked = 0

    for item in MEDICAMENTOS:
        subcat = _detect_subcat(item)
        category_id = get_or_create_category(db, subcat, ROOT)
        brand_id    = get_or_create_brand(db, item.get("brand"))
        master_id   = get_or_create_master(db, item.get("product_master"))

        cost   = safe_float(item.get("cost"))
        retail = round(cost * 1.40, 2)

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
            description=f"Medicamento: {item.get('product_master') or ''}",
            tax_percentage=0,
            ingredients=ingredients,
        )

        if was_created:
            ingredients_linked += len(ingredients)
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Medicamentos insertados:   {created}")
    print(f"⚠️  Duplicados omitidos:       {skipped}")
    print(f"🧪 Ingredientes vinculados:   {ingredients_linked}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_medicamentos(db)
    finally:
        db.close()