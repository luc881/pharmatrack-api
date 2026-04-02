import pytest


@pytest.fixture
def test_ingredient(db_session):
    from pharmatrack.models.ingredients.orm import Ingredient
    from pharmatrack.utils.slugify import slugify
    name = "paracetamol"
    ingredient = Ingredient(
        name=name,
        slug=slugify(name),
        description="Active pharmaceutical ingredient used for pain relief and fever reduction.",
    )
    db_session.add(ingredient)
    db_session.commit()
    db_session.refresh(ingredient)
    return ingredient


@pytest.fixture
def another_test_ingredient(db_session):
    from pharmatrack.models.ingredients.orm import Ingredient
    from pharmatrack.utils.slugify import slugify
    name = "ibuprofeno"
    ingredient = Ingredient(
        name=name,
        slug=slugify(name),
        description="Anti-inflammatory drug commonly used for pain relief and reducing inflammation.",
    )
    db_session.add(ingredient)
    db_session.commit()
    db_session.refresh(ingredient)
    return ingredient