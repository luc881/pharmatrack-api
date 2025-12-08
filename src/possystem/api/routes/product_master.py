from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...utils.permissions import CAN_READ_PRODUCT_MASTERS, CAN_CREATE_PRODUCT_MASTERS, CAN_UPDATE_PRODUCT_MASTERS, CAN_DELETE_PRODUCT_MASTERS
from ...models.product_master.orm import ProductMaster
from ...models.product_master.schemas import ProductMasterCreate, ProductMasterResponse, ProductMasterUpdate
from ...models.product_categories.orm import ProductCategory

db_dependency = Annotated[Session, Depends(get_db)]


router = APIRouter(
    prefix="/productsmaster",
    tags=["Products Master"]
)

@router.get("/",
            response_model=list[ProductMasterResponse],
            summary="List all product masters",
            description="Retrieve all product masters currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_PRODUCT_MASTERS)
async def read_all(db: db_dependency):
    product_masters = db.query(ProductMaster).all()
    return product_masters

@router.get(
    "/{master_id}",
    response_model=ProductMasterResponse,
    summary="Retrieve a product master by ID",
    description="Get a single Product Master record by its unique ID.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PRODUCT_MASTERS
)
async def read_product_master(
    master_id: int,
    db: db_dependency
):
    master = (
        db.query(ProductMaster)
        .filter(ProductMaster.id == master_id)
        .first()
    )

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product master {master_id} not found."
        )

    return master

@router.post(
    "/",
    response_model=ProductMasterResponse,
    summary="Create a new product master",
    description="Creates a new Product Master record in the database.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PRODUCT_MASTERS
)
async def create_product_master(
    payload: ProductMasterCreate,
    db: db_dependency
):
    # --------------------------------------------
    # 🔍 Validar si ya existe un master con el mismo nombre (opcional)
    # --------------------------------------------
    existing = db.query(ProductMaster).filter(
        ProductMaster.name.ilike(payload.name)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product master with name '{payload.name}' already exists."
        )

    # --------------------------------------------
    # 🔍 Validar que la categoría exista
    # --------------------------------------------
    category = db.query(ProductCategory).filter(
        ProductCategory.id == payload.product_category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category {payload.product_category_id} does not exist."
        )

    # --------------------------------------------
    # 🟢 Crear el registro
    # --------------------------------------------
    new_master = ProductMaster(
        name=payload.name,
        description=payload.description,
        product_category_id=payload.product_category_id
    )

    db.add(new_master)
    db.commit()
    db.refresh(new_master)

    return new_master

@router.put(
    "/{master_id}",
    response_model=ProductMasterResponse,
    summary="Update an existing product master",
    description="Updates Product Master fields. Supports partial updates.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PRODUCT_MASTERS
)
async def update_product_master(
    master_id: int,
    payload: ProductMasterUpdate,   # ahora soporta parcial
    db: db_dependency
):
    # Buscar el master
    master = (
        db.query(ProductMaster)
        .filter(ProductMaster.id == master_id)
        .first()
    )

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product master {master_id} not found."
        )

    # Obtener únicamente campos enviados
    update_data = payload.model_dump(exclude_unset=True)

    # ============================
    # Validar categoría si viene
    # ============================
    if "product_category_id" in update_data:
        category = (
            db.query(ProductCategory)
            .filter(ProductCategory.id == update_data["product_category_id"])
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product category {update_data['product_category_id']} does not exist."
            )

    # ============================
    # Validar nombre si viene
    # ============================
    if "name" in update_data:
        duplicate = (
            db.query(ProductMaster)
            .filter(
                ProductMaster.name.ilike(update_data["name"]),
                ProductMaster.id != master_id
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another product master with name '{update_data['name']}' already exists."
            )

    # ============================
    # Actualizar los campos enviados
    # ============================
    for key, value in update_data.items():
        setattr(master, key, value)

    db.commit()
    db.refresh(master)

    return master

@router.delete(
    "/{master_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product master",
    description="Deletes a product master by ID. Fails if products depend on it.",
    dependencies=CAN_DELETE_PRODUCT_MASTERS
)
async def delete_product_master(
    master_id: int,
    db: db_dependency
):
    master = db.query(ProductMaster).filter(ProductMaster.id == master_id).first()

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product master {master_id} not found."
        )

    # Intentar eliminación (puede fallar por FK si tiene dependencias)
    try:
        db.delete(master)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete product master because related products exist."
        )

    return None
