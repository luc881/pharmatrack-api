"""
pharmatrack/seeds/helpers/seeder_helpers.py

Funciones compartidas para todos los seeders.
Centraliza la lógica de get_or_create con soporte de slugs.

IMPORTANT: All lookups use slug instead of name to prevent
UniqueViolation errors when the same entity appears with
different capitalization or accents across seeders.
"""
from sqlalchemy.orm import Session

from pharmatrack.utils.slugify import slugify
from pharmatrack.utils.category_slug import build_category_slug
from pharmatrack.models.product_brand.orm import ProductBrand
from pharmatrack.models.product_categories.orm import ProductCategory
from pharmatrack.models.product_master.orm import ProductMaster
from pharmatrack.models.ingredients.orm import Ingredient
from pharmatrack.models.products.orm import Product
from pharmatrack.models.product_has_ingredients.orm import ProductHasIngredient


# =========================================================
# 🏷️ Brand
# =========================================================
def get_or_create_brand(db: Session, name: str | None) -> int | None:
    """
    Returns the brand ID for the given name, creating it if necessary.
    Looks up by slug so 'WANDEL' and 'Wandel' resolve to the same record.
    Returns None if name is empty or None.
    """
    if not name or not name.strip():
        return None

    name = name.strip()
    slug = slugify(name)

    brand = db.query(ProductBrand).filter_by(slug=slug).first()
    if not brand:
        brand = ProductBrand(name=name, slug=slug)
        db.add(brand)
        db.flush()

    return brand.id


# =========================================================
# 📂 Category
# =========================================================
def get_or_create_category(
    db: Session,
    name: str,
    parent_name: str | None = None
) -> int:
    """
    Returns the category ID for the given name + parent, creating it if necessary.
    Looks up by full-path slug (e.g. "medicamentos-antibioticos").
    """
    # Resolve parent first
    parent: ProductCategory | None = None
    if parent_name:
        parent_slug = slugify(parent_name)
        parent = db.query(ProductCategory).filter_by(slug=parent_slug).first()
        if not parent:
            parent = ProductCategory(
                name=parent_name,
                slug=parent_slug,
                parent_id=None,
                is_active=True,
            )
            db.add(parent)
            db.flush()

    # Build the full-path slug for this category
    slug = build_category_slug(name, parent.id if parent else None, db)

    # Look up by slug — handles accent and case variants
    category = db.query(ProductCategory).filter_by(slug=slug).first()
    if not category:
        category = ProductCategory(
            name=name,
            slug=slug,
            parent_id=parent.id if parent else None,
            is_active=True,
            image=None,
        )
        db.add(category)
        db.flush()

    return category.id


# =========================================================
# 🧬 Product Master
# =========================================================
def get_or_create_master(db: Session, name: str | None) -> int | None:
    """
    Returns the product master ID for the given name, creating it if necessary.
    Looks up by slug so 'Amoxicilina' and 'amoxicilina' resolve to the same record.
    Returns None if name is empty or None.
    """
    if not name or not str(name).strip():
        return None

    name = str(name).strip()
    slug = slugify(name)

    master = db.query(ProductMaster).filter_by(slug=slug).first()
    if not master:
        master = ProductMaster(name=name, slug=slug)
        db.add(master)
        db.flush()

    return master.id


# =========================================================
# 🧪 Ingredient
# =========================================================
def get_or_create_ingredient(db: Session, name: str) -> int:
    """
    Returns the ingredient ID for the given name, creating it if necessary.
    Looks up by slug so 'Extracto de Manzanilla' and 'extracto de manzanilla'
    resolve to the same record without hitting the unique slug constraint.
    """
    name = name.strip()
    slug = slugify(name)

    ingredient = db.query(Ingredient).filter_by(slug=slug).first()
    if not ingredient:
        ingredient = Ingredient(name=name, slug=slug)
        db.add(ingredient)
        db.flush()

    return ingredient.id


# =========================================================
# 📦 Product
# =========================================================
def get_or_create_product(
    db: Session,
    *,
    title: str,
    sku: str,
    brand_id: int | None,
    category_id: int,
    price_cost: float,
    price_retail: float,
    product_master_id: int | None = None,
    description: str | None = None,
    unit_name: str = "pieza",
    is_unit_sale: bool = True,
    tax_percentage: float | None = None,
    ingredients: list[dict] | None = None,
) -> tuple[Product | None, bool]:
    """
    Creates a product if the SKU does not already exist.

    Returns:
        (product, created) — created=False if the SKU was a duplicate.

    ingredients format:
        [{"name": "Amoxicilina", "amount": 500, "unit": "mg"}, ...]
    """
    # Primary duplicate check: SKU
    if db.query(Product).filter_by(sku=sku).first():
        return None, False

    # Build slug from title + sku
    parts = [title, sku] if sku else [title]
    slug = slugify(" ".join(parts))

    # Secondary duplicate check: slug (same title+sku, different casing)
    if db.query(Product).filter_by(slug=slug).first():
        return None, False

    product = Product(
        title=title,
        slug=slug,
        sku=sku,
        brand_id=brand_id,
        product_category_id=category_id,
        product_master_id=product_master_id,
        price_cost=price_cost,
        price_retail=price_retail,
        unit_name=unit_name,
        is_unit_sale=is_unit_sale,
        description=description,
        tax_percentage=tax_percentage,
    )

    db.add(product)
    db.flush()  # get product.id before linking ingredients

    if ingredients:
        for ing in ingredients:
            ing_name = str(ing.get("name") or "").strip()
            if not ing_name:
                continue

            ing_id = get_or_create_ingredient(db, ing_name)

            db.add(ProductHasIngredient(
                product_id=product.id,
                ingredient_id=ing_id,
                amount=ing.get("amount"),
                unit=ing.get("unit"),
            ))

    return product, True


# =========================================================
# 🔢 Utility
# =========================================================
def safe_float(value, default: float = 0.0) -> float:
    """Safely converts a value to float, returning default on failure."""
    try:
        if value is None:
            return default
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default