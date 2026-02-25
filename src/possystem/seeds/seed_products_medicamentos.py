from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.products.orm import Product
from possystem.models.product_brand.orm import ProductBrand
from possystem.models.product_categories.orm import ProductCategory
from possystem.models.ingredients.orm import Ingredient
from possystem.models.product_master.orm import ProductMaster
from possystem.models.product_has_ingredients.orm import ProductHasIngredient

# ---------------------------
# JSON DATA
# ---------------------------
from possystem.seeds.data.medicamentos_json import MEDICAMENTOS


# ---------------------------
# AUTO SUBCATEGORY RULES
# ---------------------------
AUTO_SUBCATEGORY = {
    # Antibióticos
    "Amoxicilina": "Antibióticos",
    "Cloranfenicol": "Antibióticos",
    "Cefalexina": "Antibióticos",
    "Ciprofloxacino": "Antibióticos",
    "Claritromicina": "Antibióticos",
    "Eritromicina": "Antibióticos",
    "Gentamicina": "Antibióticos",
    "Lincomicina": "Antibióticos",
    "Ampicilina": "Antibióticos",
    "Ceftriaxona": "Antibióticos",
    "Cefotaxima": "Antibióticos",
    "Cefalotina": "Antibióticos",
    "Ceftazidima": "Antibióticos",
    "Fosfomicina": "Antibióticos",
    "Doxiciclina": "Antibióticos",
    "Azitromicina": "Antibióticos",

    # Analgésicos
    "Paracetamol": "Analgésicos",
    "Ácido Acetilsalicílico": "Analgésicos",
    "Metamizol": "Analgésicos",
    "Ketorolaco": "Analgésicos",
    "Tramadol": "Analgésicos",

    # Antiinflamatorios
    "Diclofenaco": "Antiinflamatorios",
    "Ibuprofeno": "Antiinflamatorios",
    "Meloxicam": "Antiinflamatorios",

    # Gastrointestinales
    "Omeprazol": "Gastrointestinales",
    "Pantoprazol": "Gastrointestinales",

    # Antialérgicos
    "Loratadina": "Antialérgicos",
    "Cetirizina": "Antialérgicos",

    # Oftalmológicos
    "Tobramicina": "Oftalmológicos",
    "Hipromelosa": "Oftalmológicos",
}


# ---------------------------
# HELPERS
# ---------------------------

def get_or_create_brand(db: Session, name: str | None) -> int | None:
    if not name or not name.strip():
        return None  # no crear marca si no existe

    name = name.strip()

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
        category = ProductCategory(
            name=name,
            parent_id=parent.id if parent else None
        )
        db.add(category)
        db.commit()
        db.refresh(category)

    return category.id


def get_or_create_master(db: Session, name: str | None) -> int | None:
    if not name or not str(name).strip():
        return None  # no crear master si no existe

    name = str(name).strip()

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


def auto_detect_subcategory(product_master: str | None, title: str | None) -> str | None:
    if not product_master:
        return None

    product_master = product_master.lower()
    title = (title or "").lower()

    mapping = {
        "paracetamol": "Analgésicos",
        "ibuprofeno": "Antiinflamatorios",
        "amoxicilina": "Antibióticos",
        # agrega los tuyos aquí
    }

    for key, value in mapping.items():
        if key in product_master or key in title:
            return value

    return None

def safe_float(value, default: float = 0.0) -> float:
    """
    Convierte un valor a float.
    Si es None, vacío o inválido, devuelve el default (0.0).
    """
    try:
        if value is None:
            return default

        value = str(value).strip()

        if value == "":
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


# ---------------------------
# SEEDER PRINCIPAL
# ---------------------------

def seed_medicamentos(db: Session):

    try:
        root_category = "Medicamentos"

        created = 0
        skipped = 0
        ingredients_linked = 0

        for item in MEDICAMENTOS:

            # Evitar duplicados por SKU
            if db.query(Product).filter_by(sku=item["sku"]).first():
                skipped += 1
                continue

            # BRAND
            brand_id = get_or_create_brand(db, item.get("brand"))

            # PRODUCT MASTER
            master_id = get_or_create_master(db, item.get("product_master"))

            # SUBCATEGORY
            subcat = item.get("category")

            if not subcat:
                subcat = auto_detect_subcategory(
                    item["product_master"],
                    item["title"]
                ) or "Analgésicos"

            category_id = get_or_create_category(db, subcat, root_category)

            # PRECIOS
            cost = safe_float(item.get("cost"))
            retail = round(cost * 1.40, 2)  # margen farmacia más conservador

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
                description=f"Medicamento: {item['product_master']}",
                tax_percentage=0,
            )

            db.add(product)
            db.flush()

            # INGREDIENTES
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
                ingredients_linked += 1

            created += 1

        db.commit()

        print(f"✅ Medicamentos insertados: {created}")
        print(f"⚠️ Duplicados omitidos: {skipped}")
        print(f"🧪 Ingredientes vinculados: {ingredients_linked}")

    except Exception as e:
        db.rollback()
        raise e


# ---------------------------
# RUN
# ---------------------------

if __name__ == "__main__":
    db = SessionLocal()
    seed_medicamentos(db)
    db.close()