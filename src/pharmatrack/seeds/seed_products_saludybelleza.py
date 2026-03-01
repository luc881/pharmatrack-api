"""
pharmatrack/seeds/seed_products_saludybelleza.py

NOTE: SALUD_BELLEZA data list is unchanged from the original file.
      Only the helper functions and product creation logic were refactored.
"""
from sqlalchemy.orm import Session
from pharmatrack.db.session import SessionLocal
from pharmatrack.seeds.helpers.seeder_helpers import (
    get_or_create_brand,
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Cuidado personal y belleza"

# ── paste your full SALUD_BELLEZA list here (unchanged) ──────────────────────
SALUD_BELLEZA: list[dict] = [
    # ... (same data as original seed_products_saludybelleza.py)
]
# ─────────────────────────────────────────────────────────────────────────────


def _classify(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["pasta", "cepillo", "listerine", "sensodyne", "hilo dental", "orthowax", "gum"]):
        return "Higiene dental"
    if any(x in t for x in ["condon", "prudence", "sico", "lubricante"]):
        return "Salud sexual"
    if any(x in t for x in ["bebe", "chupon", "mamila", "huggies", "ricitos", "suavelastic", "absorsec", "pañal"]):
        return "Bebé y maternidad"
    if any(x in t for x in ["pantene", "savile", "elvive", "shampoo", "cabrice", "caprice", "sedal", "wildroot", "brillantina"]):
        return "Cabello"
    if any(x in t for x in ["crema", "nivea", "ponds", "lubriderm", "teatrical", "vaseline", "locion", "aceite", "gel antiseptico", "protector solar"]):
        return "Cuidado de la piel"
    if any(x in t for x in ["corta una", "alicate", "pinza", "lima", "peine", "rastrillo", "espuma de afeitar", "rasuradora"]):
        return "Accesorios y herramientas"
    if any(x in t for x in ["cateter", "contador de pastillas", "clearblue"]):
        return "Dispositivos médicos"
    return "Higiene personal"


def seed_salud_belleza(db: Session):
    created = skipped = 0

    for item in SALUD_BELLEZA:
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
            description="Producto salud y belleza precargado",
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Salud y belleza insertados: {created}")
    print(f"⚠️  Duplicados omitidos:        {skipped}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_salud_belleza(db)
    finally:
        db.close()