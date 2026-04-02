import pytest
from pharmatrack.models.products.schemas import _product_slug
from pharmatrack.utils.slugify import slugify


# =========================================================
# 🔹 Fixture de categoría (prerequisito de productos)
# =========================================================

@pytest.fixture
def test_product_category(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory

    category = ProductCategory(
        name="General",
        slug=slugify("General"),
        is_active=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


# =========================================================
# 🔹 Fixtures de productos
# =========================================================

@pytest.fixture
def test_product(db_session, test_product_category):
    from pharmatrack.models.products.orm import Product

    product = Product(
        title="Refresco Cola 600ml",
        slug=_product_slug("Refresco Cola 600ml", "COLA600ML"),
        sku="COLA600ML",
        image="https://example.com/images/cola600.png",
        price_retail=20.0,
        price_cost=18.0,
        description="Refresco de cola en presentación de 600ml",
        is_active=True,
        is_unit_sale=True,
        unit_name="pieza",
        product_category_id=test_product_category.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def another_product(db_session, test_product_category):
    from pharmatrack.models.products.orm import Product

    product = Product(
        title="Galletas de Chocolate",
        slug=_product_slug("Galletas de Chocolate", "GALLETASCHOC"),
        sku="GALLETASCHOC",
        image="https://example.com/images/galletas_chocolate.png",
        price_retail=15.0,
        price_cost=13.0,
        description="Deliciosas galletas de chocolate",
        is_active=True,
        is_unit_sale=True,
        unit_name="pieza",
        product_category_id=test_product_category.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def product_with_ingredients(db_session, test_product_category, test_ingredient, another_test_ingredient):
    from pharmatrack.models.products.orm import Product
    from pharmatrack.models.product_has_ingredients.orm import ProductHasIngredient

    product = Product(
        title="Medicamento Combinado",
        slug=_product_slug("Medicamento Combinado", "MEDCOMBINADO"),
        sku="MEDCOMBINADO",
        image="https://example.com/images/medicamento_combinado.png",
        price_retail=50.0,
        price_cost=40.0,
        description="Medicamento que combina varios ingredientes activos",
        is_active=True,
        is_unit_sale=True,
        unit_name="pieza",
        product_category_id=test_product_category.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    assoc1 = ProductHasIngredient(
        product_id=product.id,
        ingredient_id=test_ingredient.id,
        amount=500,
        unit="mg",
    )
    assoc2 = ProductHasIngredient(
        product_id=product.id,
        ingredient_id=another_test_ingredient.id,
        amount=5,
        unit="mg",
    )
    db_session.add_all([assoc1, assoc2])
    db_session.commit()
    db_session.refresh(product)
    return product