# possystem/seeders/helpers/services.py

from sqlalchemy.orm import Session
from possystem.models.product_categories.orm import ProductCategory
from possystem.models.products.orm import Product


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


def create_service(
    db: Session,
    sku: str,
    title: str,
    price: float,
    category_id: int,
):
    """
    Inserta un servicio médico como Product sin stock.
    """

    if db.query(Product).filter_by(sku=sku).first():
        return None  # ya existe

    service = Product(
        sku=sku,
        title=title,
        brand_id=None,  # servicios no tienen marca
        product_category_id=category_id,
        price_cost=0,  # opcional
        price_retail=price,
        unit_name="servicio",
        is_unit_sale=True,
        description="Servicio médico en farmacia",
    )

    db.add(service)
    return service