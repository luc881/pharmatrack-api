


from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.products.orm import Product
from possystem.models.product_brand.orm import ProductBrand
from possystem.models.product_categories.orm import ProductCategory
from possystem.models.ingredients.orm import Ingredient
from possystem.models.product_master.orm import ProductMaster
from possystem.models.product_has_ingredients.orm import ProductHasIngredient

# ---------------------------
# JSON DATA (ejemplo)
# ---------------------------
from possystem.seeds.data.suplementos_json import SUPLEMENTOS

# ---------------------------
# Auto Subcategory Rules
# ---------------------------
AUTO_SUBCATEGORY = {
    "Vitamina": "Vitaminas",
    "Multivitamínico": "Vitaminas",
    "Calcio": "Minerales",
    "Magnesio": "Minerales",
    "Hierro": "Minerales",
    "Omega": "Omega y lípidos",
    "DHA": "Omega y lípidos",
    "Colágeno": "Colágeno y belleza",
    "Melatonina": "Salud del sueño",
    "Fibra": "Salud digestiva",
    "Probióticos": "Probióticos y prebióticos",
    "Pediasure": "Nutrición infantil",
    "Ensure": "Nutrición especializada",
    "Glucerna": "Nutrición especializada"
}

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


def get_or_create_master(db: Session, name: str) -> int:
    master = db.query(ProductMaster).filter_by(name=name).first()
    if not master:
        master = ProductMaster(name=name)
        db.add(master)
        db.commit()
        db.refresh(master)
    return master.id


def get_or_create_ingredient(db: Session, name: str) -> int:
    ingredient = db.query(Ingredient).filter_by(name=name).first()
    if not ingredient:
        ingredient = Ingredient(name=name)
        db.add(ingredient)
        db.commit()
        db.refresh(ingredient)
    return ingredient.id


def auto_detect_subcategory(title: str) -> str | None:
    title_lower = title.lower()
    for key, subcat in AUTO_SUBCATEGORY.items():
        if key.lower() in title_lower:
            return subcat
    return None


# ---------------------------
# Seeder principal
# ---------------------------

def seed_suplementos(db: Session):

    try:
        root_category = "Suplementos y nutrición"

        created = 0
        skipped = 0
        ingredients_created = 0

        for item in SUPLEMENTOS:

            # Duplicado SKU
            if db.query(Product).filter_by(sku=item["sku"]).first():
                skipped += 1
                continue

            # BRAND
            brand_id = get_or_create_brand(db, item["brand"])

            # PRODUCT MASTER
            master_id = get_or_create_master(db, item["product_master"])

            # CATEGORY ROOT
            subcat = item.get("subcategory")

            # Auto detect fallback
            if not subcat:
                subcat = auto_detect_subcategory(item["title"]) or "Vitaminas"

            category_id = get_or_create_category(db, subcat, root_category)

            # PRICES
            cost = float(item["cost"])
            retail = round(cost * 1.45, 2)

            # PRODUCT
            product = Product(
                title=item["title"],
                sku=item["sku"],
                brand_id=brand_id,
                product_category_id=category_id,
                product_master_id=master_id,
                price_cost=cost,
                price_retail=retail,
                unit_name="pieza",
                is_unit_sale=True,
                description=f"Suplemento: {item['product_master']}",
            )

            db.add(product)
            db.flush()  # obtener product.id sin commit

            # INGREDIENTS
            for ing in item.get("ingredients", []):
                ing_name = ing["name"].strip()
                ing_id = get_or_create_ingredient(db, ing_name)

                link = ProductHasIngredient(
                    product_id=product.id,
                    ingredient_id=ing_id,
                    amount=ing.get("amount"),
                    unit=ing.get("unit"),
                )
                db.add(link)

                ingredients_created += 1

            created += 1

        db.commit()

        print(f"✅ Suplementos insertados: {created}")
        print(f"⚠️ Duplicados omitidos: {skipped}")
        print(f"🧪 Ingredientes vinculados: {ingredients_created}")

    except Exception as e:
        db.rollback()
        raise e


# ---------------------------
# RUN
# ---------------------------

if __name__ == "__main__":
    db = SessionLocal()
    seed_suplementos(db)
    db.close()