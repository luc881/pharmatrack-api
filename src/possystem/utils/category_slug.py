from sqlalchemy.orm import Session
from possystem.utils.slugify import slugify


def build_category_slug(name: str, parent_id: int | None, db: Session) -> str:
    """
    Builds a full-path slug for a category by walking up the parent tree.

    Examples:
        "Antibióticos"  (parent=None)              → "antibioticos"
        "Antibióticos"  (parent slug="medicamentos")→ "medicamentos-antibioticos"
        "Orales"        (parent slug="medicamentos-antibioticos") → "medicamentos-antibioticos-orales"

    Args:
        name:      The category name to slugify.
        parent_id: The parent category ID, or None for root categories.
        db:        SQLAlchemy session used to walk up the tree.

    Returns:
        A unique full-path slug string.
    """
    # Import here to avoid circular imports at module level
    from possystem.models.product_categories.orm import ProductCategory

    name_slug = slugify(name)

    if parent_id is None:
        return name_slug

    # Walk up the parent chain collecting slugs
    path_parts: list[str] = []
    current_id: int | None = parent_id

    while current_id is not None:
        parent = db.get(ProductCategory, current_id)
        if parent is None:
            break
        path_parts.append(slugify(parent.name))
        current_id = parent.parent_id

    # Reverse so it reads root → leaf
    path_parts.reverse()
    path_parts.append(name_slug)

    return "-".join(path_parts)


def rebuild_category_slug(category_id: int, db: Session) -> str:
    """
    Rebuilds the slug for an EXISTING category (used on updates).
    Reads the current name and parent_id from the DB record.
    """
    from possystem.models.product_categories.orm import ProductCategory

    category = db.get(ProductCategory, category_id)
    if category is None:
        raise ValueError(f"Category {category_id} not found")

    return build_category_slug(category.name, category.parent_id, db)


def rebuild_children_slugs(category_id: int, db: Session) -> None:
    """
    Recursively updates the slugs of ALL descendants of a category.
    Call this after renaming a category or changing its parent,
    since the full-path slug of every child is affected.

    Example:
        "medicamentos-antibioticos-orales"
        If "medicamentos" is renamed to "farmacos", all children
        must become "farmacos-antibioticos-orales".
    """
    from possystem.models.product_categories.orm import ProductCategory

    children = db.query(ProductCategory).filter(
        ProductCategory.parent_id == category_id
    ).all()

    for child in children:
        child.slug = build_category_slug(child.name, child.parent_id, db)
        rebuild_children_slugs(child.id, db)  # recurse into grandchildren