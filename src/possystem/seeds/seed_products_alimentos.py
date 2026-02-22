from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.products.orm import Product
from possystem.models.product_brand.orm import ProductBrand
from possystem.models.product_categories.orm import ProductCategory

# ---------------------------
# Datos crudos (Excel normalizado)
# ---------------------------
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

def seed_golosinas(db: Session):

    try:
        # ROOT
        alimentos_id = get_or_create_category(db, "Alimentos y bebidas")

        # SUBCATEGORÍAS
        chocolates_id = get_or_create_category(db, "Chocolates", "Alimentos y bebidas")
        caramelos_id = get_or_create_category(db, "Caramelos y chicles", "Alimentos y bebidas")
        bebidas_id = get_or_create_category(db, "Bebidas", "Alimentos y bebidas")
        paletas_id = get_or_create_category(db, "Paletas", "Alimentos y bebidas")
        otros_id = get_or_create_category(db, "Otros dulces", "Alimentos y bebidas")

        created = 0
        skipped = 0

        for item in GOLOSINAS:
            if db.query(Product).filter_by(sku=item["sku"]).first():
                skipped += 1
                continue

            brand_id = get_or_create_brand(db, item["brand"])

            title = item["title"].lower()

            if "electrolit" in title or "agua" in title:
                category_id = bebidas_id
            elif "paleta" in title:
                category_id = paletas_id
            elif any(x in title for x in ["ferrero", "snickers", "milky", "kitkat", "m&m", "turin"]):
                category_id = chocolates_id
            elif any(x in title for x in ["clorets", "halls", "trident", "frescas", "larin"]):
                category_id = caramelos_id
            else:
                category_id = otros_id

            cost = float(item["cost"])
            retail = round(cost * 1.40, 2)

            product = Product(
                title=item["title"],
                sku=item["sku"],
                brand_id=brand_id,
                product_category_id=category_id,
                price_cost=cost,
                price_retail=retail,
                unit_name="pieza",
                is_unit_sale=True,
                description="Producto de golosina precargado",
            )

            db.add(product)
            created += 1

        db.commit()
        print(f"✅ Golosinas insertadas: {created}")
        print(f"⚠️ Duplicados omitidos: {skipped}")

    except Exception as e:
        db.rollback()
        raise e



if __name__ == "__main__":
    seed_golosinas()
