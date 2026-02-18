from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...models.product_categories.orm import ProductCategory
from ...models.product_categories.schemas import ProductCategoryCreate, ProductCategoryResponse, ProductCategoryUpdate, ProductCategoryTreeResponse
from ...utils.permissions import CAN_READ_PRODUCT_CATEGORIES, CAN_CREATE_PRODUCT_CATEGORIES, CAN_UPDATE_PRODUCT_CATEGORIES, CAN_DELETE_PRODUCT_CATEGORIES
from ...utils.product_categories_tree import build_category_tree, serialize_category_tree

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/productscategories",
    tags=["Products Categories"]
)

@router.get("/",
            response_model=list[ProductCategoryResponse],
            summary="List all product categories",
            description="Retrieve all product categories currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_CATEGORIES
            )
async def read_all(db: db_dependency):
    product_categories = db.query(ProductCategory).all()
    return product_categories

@router.get(
    "/tree",
    response_model=list[ProductCategoryTreeResponse],
    summary="Get category tree",
)
async def get_category_tree(db: db_dependency):
    categories = db.query(ProductCategory).all()
    tree = build_category_tree(categories)
    return tree

@router.get(
    "/roots",
    response_model=list[ProductCategoryResponse],
    summary="Get root categories",
)
async def get_root_categories(db: db_dependency):
    roots = db.query(ProductCategory).filter(ProductCategory.parent_id == None).all()
    return roots




@router.get(
    "/{category_id}",
    response_model=ProductCategoryResponse,
    summary="Get category by ID",
    description="Retrieve a single product category by its ID.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PRODUCT_CATEGORIES,
)
async def read_one(category_id: int, db: db_dependency):
    category = db.get(ProductCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category

@router.get(
    "/{category_id}/tree",
    response_model=ProductCategoryTreeResponse,
)
async def get_subtree(category_id: int, db: db_dependency):
    categories = db.query(ProductCategory).all()
    root = db.get(ProductCategory, category_id)

    if not root:
        raise HTTPException(404, "Category not found")

    tree = build_category_tree(categories, root.id)

    return {
        "id": root.id,
        "name": root.name,
        "image": root.image,
        "is_active": root.is_active,
        "children": tree,
    }





@router.post("/",
                response_model=ProductCategoryResponse,
                summary="Create a new product category",
                description="Create a new product category with the provided details.",
                status_code=status.HTTP_201_CREATED,
                dependencies=CAN_CREATE_PRODUCT_CATEGORIES
                )
async def create(product_category: ProductCategoryCreate, db: db_dependency):
    existing_category = db.query(ProductCategory).filter(ProductCategory.name == product_category.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product category with this name already exists."
        )
    new_category = ProductCategory(**product_category.model_dump(mode="json"))
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put(
    "/{category_id}",
    response_model=ProductCategoryResponse,
    summary="Update an existing product category",
    description="Update the details of an existing product category.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PRODUCT_CATEGORIES,
)
async def update(category_id: int, product_category: ProductCategoryUpdate, db: db_dependency):
    existing_category = db.get(ProductCategory, category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product category not found.",
        )

    # ✅ Check for duplicate names if name is provided
    if product_category.name:
        name_conflict = db.query(ProductCategory).filter(
            ProductCategory.name == product_category.name,
            ProductCategory.id != category_id
        ).first()
        if name_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another product category with this name already exists.",
            )

    # ✅ More compact update logic (like in products)
    update_data = product_category.model_dump(exclude_unset=True, mode="json")
    for key, value in update_data.items():
        setattr(existing_category, key, value)

    db.commit()
    db.refresh(existing_category)
    return existing_category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product category",
    description="Delete an existing product category by its ID.",
    dependencies=CAN_DELETE_PRODUCT_CATEGORIES
)
async def delete(category_id: int, db: db_dependency):
    existing_category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product category not found."
        )
    db.delete(existing_category)
    db.commit()
    return None