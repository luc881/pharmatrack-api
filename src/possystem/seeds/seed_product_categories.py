from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.product_categories.orm import ProductCategory


# --- Categorías base de la farmacia ---
PRODUCT_CATEGORIES = [
    {
        "name": "medicamentos",
        "image": None,
        "is_active": True,
    },
    {
        "name": "material de curacion y dispositivos medicos",
        "image": None,
        "is_active": True,
    },
    {
        "name": "cuidado personal y belleza",
        "image": None,
        "is_active": True,
    },
    {
        "name": "suplementos y nutricion",
        "image": None,
        "is_active": True,
    },
    {
        "name": "alimentos y bebidas",
        "image": None,
        "is_active": True,
    },
    {
        "name": "servicios farmaceuticos",
        "image": None,
        "is_active": True,
    },
    {
        "name": "otros",
        "image": None,
        "is_active": True,
    },
]



def seed_product_categories(db: Session):
    """
    Inserta las categorías base de productos.
    No duplica categorías existentes por nombre.
    """
    created_count = 0

    for category_data in PRODUCT_CATEGORIES:
        exists = (
            db.query(ProductCategory)
            .filter(ProductCategory.name == category_data["name"])
            .first()
        )

        if not exists:
            category = ProductCategory(**category_data)
            db.add(category)
            created_count += 1

    db.commit()
    print(f"✅ Seeding completado: {created_count} nuevas categorías creadas.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_product_categories(db)
    finally:
        db.close()
