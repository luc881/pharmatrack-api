import pytest

# --- Fixture for creating a sample product has ingredients relationship ---

import pytest

@pytest.fixture
def product_has_ingredient(db_session, test_product, test_ingredient):
    from pharmatrack.models.product_has_ingredients.orm import product_has_ingredients

    relation = product_has_ingredients(
        product_id=test_product.id,
        ingredient_id=test_ingredient.id,
        quantity=1  # Cambia si tu tabla no usa este campo
    )

    db_session.add(relation)
    db_session.commit()
    db_session.refresh(relation)

    return relation


@pytest.fixture
def another_product_has_ingredient(db_session, another_product, another_test_ingredient):
    from pharmatrack.models.product_has_ingredients.orm import product_has_ingredients

    relation = product_has_ingredients(
        product_id=another_product.id,
        ingredient_id=another_test_ingredient.id,
        quantity=2  # ajusta este campo si no existe
    )

    db_session.add(relation)
    db_session.commit()
    db_session.refresh(relation)

    return relation
