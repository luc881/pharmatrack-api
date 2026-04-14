from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...models.product_categories.orm import ProductCategory
from ...models.product_categories.schemas import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryUpdate,
    ProductCategoryTreeResponse,
    PaginatedResponse,
    PaginationParams,
)
from ...utils.permissions import (
    CAN_READ_PRODUCT_CATEGORIES,
    CAN_CREATE_PRODUCT_CATEGORIES,
    CAN_UPDATE_PRODUCT_CATEGORIES,
    CAN_DELETE_PRODUCT_CATEGORIES,
)
from ...utils.product_categories_tree import build_category_tree, check_category_cycle
from ...utils.category_slug import build_category_slug, rebuild_children_slugs
from pharmatrack.utils.pagination import paginate

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/productscategories",
    tags=["Products Categories"]
)


# =========================================================
# GET /
# =========================================================
@router.get("",
            response_model=PaginatedResponse[ProductCategoryResponse],
            summary="List all product categories",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_CATEGORIES)
async def read_all(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(ProductCategory).order_by(ProductCategory.name.asc())
    return paginate(query, pagination)


# =========================================================
# GET /tree  — sin paginar (árbol completo siempre)
# =========================================================
@router.get("/tree",
            response_model=list[ProductCategoryTreeResponse],
            summary="Get full category tree",
            dependencies=CAN_READ_PRODUCT_CATEGORIES)
async def get_category_tree(db: db_dependency):
    categories = db.query(ProductCategory).all()
    return build_category_tree(categories)


# =========================================================
# GET /roots
# =========================================================
@router.get("/roots",
            response_model=PaginatedResponse[ProductCategoryResponse],
            summary="Get root categories",
            dependencies=CAN_READ_PRODUCT_CATEGORIES)
async def get_root_categories(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(ProductCategory).filter(
        ProductCategory.parent_id.is_(None)
    ).order_by(ProductCategory.name.asc())
    return paginate(query, pagination)


# =========================================================
# GET /{category_id}
# =========================================================
@router.get("/{category_id}",
            response_model=ProductCategoryResponse,
            summary="Get category by ID",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_CATEGORIES)
async def read_one(category_id: int, db: db_dependency):
    category = db.get(ProductCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category


# =========================================================
# GET /{category_id}/tree  — sin paginar (subárbol siempre completo)
# =========================================================
@router.get("/{category_id}/tree",
            response_model=ProductCategoryTreeResponse,
            summary="Get subtree from a category",
            dependencies=CAN_READ_PRODUCT_CATEGORIES)
async def get_subtree(category_id: int, db: db_dependency):
    root = db.get(ProductCategory, category_id)
    if not root:
        raise HTTPException(status_code=404, detail="Category not found.")

    categories = db.query(ProductCategory).all()
    tree = build_category_tree(categories, root.id)

    return {
        "id": root.id,
        "name": root.name,
        "slug": root.slug,
        "image": root.image,
        "is_active": root.is_active,
        "parent_id": root.parent_id,
        "children": tree,
    }


# =========================================================
# POST /
# =========================================================
@router.post("",
             response_model=ProductCategoryResponse,
             summary="Create a new product category",
             status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_PRODUCT_CATEGORIES)
async def create(product_category: ProductCategoryCreate, db: db_dependency):
    if product_category.parent_id is not None:
        parent = db.get(ProductCategory, product_category.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found.")

    slug = build_category_slug(product_category.name, product_category.parent_id, db)

    if db.query(ProductCategory).filter(ProductCategory.slug == slug).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists in this path."
        )

    new_category = ProductCategory(
        **product_category.model_dump(mode="json"),
        slug=slug
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


# =========================================================
# PUT /{category_id}
# =========================================================
@router.put("/{category_id}",
            response_model=ProductCategoryResponse,
            summary="Update an existing product category",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_PRODUCT_CATEGORIES)
async def update(category_id: int, product_category: ProductCategoryUpdate, db: db_dependency):
    existing_category = db.get(ProductCategory, category_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Product category not found.")

    if product_category.parent_id is not None:
        if product_category.parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent.")

        parent = db.get(ProductCategory, product_category.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found.")

        check_category_cycle(db, category_id, product_category.parent_id)

    final_name = product_category.name or existing_category.name
    final_parent_id = (
        product_category.parent_id
        if product_category.parent_id is not None
        else existing_category.parent_id
    )

    name_changed = product_category.name is not None and product_category.name != existing_category.name
    parent_changed = product_category.parent_id is not None and product_category.parent_id != existing_category.parent_id

    if name_changed or parent_changed:
        new_slug = build_category_slug(final_name, final_parent_id, db)

        conflict = db.query(ProductCategory).filter(
            ProductCategory.slug == new_slug,
            ProductCategory.id != category_id
        ).first()
        if conflict:
            raise HTTPException(
                status_code=400,
                detail="A category with this name already exists in this path."
            )

        existing_category.slug = new_slug
        db.flush()
        rebuild_children_slugs(category_id, db)

    update_data = product_category.model_dump(exclude_unset=True, mode="json")
    for key, value in update_data.items():
        setattr(existing_category, key, value)

    db.commit()
    db.refresh(existing_category)
    return existing_category


# =========================================================
# DELETE /{category_id}
# =========================================================
@router.delete("/{category_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a product category",
               dependencies=CAN_DELETE_PRODUCT_CATEGORIES)  # ✅ faltaba
async def delete(category_id: int, db: db_dependency):
    category = db.get(ProductCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Product category not found.")

    has_children = db.query(ProductCategory).filter(
        ProductCategory.parent_id == category_id
    ).first()
    if has_children:
        raise HTTPException(status_code=400, detail="Cannot delete a category that has subcategories.")

    db.delete(category)
    db.commit()