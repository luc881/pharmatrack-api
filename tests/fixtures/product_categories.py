import pytest


@pytest.fixture
def test_product_category(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    category = ProductCategory(
        name="Analgésicos",
        slug=slugify("Analgésicos"),
        image="http://example.com/analgesicos.png",
        is_active=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def another_product_category(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    category = ProductCategory(
        name="Antibióticos",
        slug=slugify("Antibióticos"),
        image="http://example.com/antibioticos.png",
        is_active=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def category_root(db_session):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.slugify import slugify
    root = ProductCategory(
        name="Medicamentos",
        slug=slugify("Medicamentos"),
        image=None,
        is_active=True,
        parent_id=None,
    )
    db_session.add(root)
    db_session.commit()
    db_session.refresh(root)
    return root


@pytest.fixture
def category_child(db_session, category_root):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.category_slug import build_category_slug
    slug = build_category_slug("Analgésicos", category_root.id, db_session)
    child = ProductCategory(
        name="Analgésicos",
        slug=slug,
        image=None,
        is_active=True,
        parent_id=category_root.id,
    )
    db_session.add(child)
    db_session.commit()
    db_session.refresh(child)
    return child


@pytest.fixture
def category_subchild(db_session, category_child):
    from pharmatrack.models.product_categories.orm import ProductCategory
    from pharmatrack.utils.category_slug import build_category_slug
    slug = build_category_slug("Paracetamol", category_child.id, db_session)
    subchild = ProductCategory(
        name="Paracetamol",
        slug=slug,
        image=None,
        is_active=True,
        parent_id=category_child.id,
    )
    db_session.add(subchild)
    db_session.commit()
    db_session.refresh(subchild)
    return subchild