from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.products.orm import Product
from possystem.models.product_brand.orm import ProductBrand
from possystem.models.product_categories.orm import ProductCategory

# ---------------------------
# Datos crudos
# ---------------------------

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

# ---------------------------
# Helpers
# ---------------------------

def get_or_create_brand(db: Session, name: str) -> int:
    brand = db.query(ProductBrand).filter_by(name=name).first()
    if not brand:
        brand = ProductBrand(name=name)
        db.add(brand)
        db.commit()
        db.refresh(brand)
    return brand.id


def get_or_create_category(db: Session, name: str, parent_name: str | None = None) -> int:
    parent = None
    if parent_name:
        parent = db.query(ProductCategory).filter_by(name=parent_name).first()
        if not parent:
            parent = ProductCategory(name=parent_name)
            db.add(parent)
            db.commit()
            db.refresh(parent)

    category = db.query(ProductCategory).filter_by(name=name).first()
    if not category:
        category = ProductCategory(name=name, parent_id=parent.id if parent else None)
        db.add(category)
        db.commit()
        db.refresh(category)

    return category.id


# ---------------------------
# Seeder principal
# ---------------------------

def seed_otros(db: Session):

    try:
        # ROOT
        misc_id = get_or_create_category(db, "Miscelánea y hogar")

        # SUBCATEGORÍAS
        pilas_id = get_or_create_category(db, "Pilas y energía", "Miscelánea y hogar")
        limpieza_id = get_or_create_category(db, "Limpieza y desinfección", "Miscelánea y hogar")
        papeleria_id = get_or_create_category(db, "Papelería y oficina", "Miscelánea y hogar")
        ferreteria_id = get_or_create_category(db, "Adhesivos y ferretería ligera", "Miscelánea y hogar")
        higiene_id = get_or_create_category(db, "Higiene del hogar", "Miscelánea y hogar")
        veterinaria_id = get_or_create_category(db, "Veterinaria", "Miscelánea y hogar")
        otros_id = get_or_create_category(db, "Otros", None)

        created = 0
        skipped = 0

        for item in OTROS_PRODUCTOS:
            if db.query(Product).filter_by(sku=item["sku"]).first():
                skipped += 1
                continue

            brand_id = get_or_create_brand(db, item["brand"])

            title = item["title"].lower()

            # Clasificación automática
            if any(x in title for x in ["duracell", "eveready", "pila", "9v", "aa", "aaa"]):
                category_id = pilas_id
            elif any(x in title for x in ["amoniaco", "borax", "bicarbonato", "lysol", "cloro", "raid"]):
                category_id = limpieza_id
            elif any(x in title for x in ["liga"]):
                category_id = papeleria_id
            elif any(x in title for x in ["kolaloka", "encendedor"]):
                category_id = ferreteria_id
            elif any(x in title for x in ["papel", "kleenex", "sanitas"]):
                category_id = higiene_id
            elif "veterinario" in title:
                category_id = veterinaria_id
            else:
                category_id = otros_id

            cost = float(item["cost"])
            retail = round(cost * 1.40, 2) if cost > 0 else 0

            product = Product(
                title=item["title"],
                sku=item["sku"],
                brand_id=brand_id,
                product_category_id=category_id,
                price_cost=cost,
                price_retail=retail,
                unit_name="pieza",
                is_unit_sale=True,
                description="Producto misceláneo precargado",
            )

            db.add(product)
            created += 1

        db.commit()
        print(f"✅ Otros productos insertados: {created}")
        print(f"⚠️ Duplicados omitidos: {skipped}")

    except Exception as e:
        db.rollback()
        raise e


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_otros(db)
    finally:
        db.close()