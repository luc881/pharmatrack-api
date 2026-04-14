from fastapi import Depends, HTTPException, APIRouter, Response
from typing import Annotated
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import get_db
from ...utils.permissions import (
    CAN_READ_PRODUCT_BATCHES,
    CAN_CREATE_PRODUCT_BATCHES,
    CAN_UPDATE_PRODUCT_BATCHES,
    CAN_DELETE_PRODUCT_BATCHES,
)
from ...models.product_batch.orm import ProductBatch
from ...models.product_batch.schemas import (
    ProductBatchCreate,
    ProductBatchResponse,
    ProductBatchUpdate,
    ProductBatchDetailsResponse,
    PaginatedResponse,
    PaginationParams,
)
from ...models.products.orm import Product
from pharmatrack.utils.pagination import paginate


db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/productsbatches",
    tags=["Products Batches"]
)


# ---------------------------------------------------------------------
# GET ALL PRODUCT BATCHES
# ---------------------------------------------------------------------
@router.get(
    "",
    response_model=PaginatedResponse[ProductBatchResponse],
    summary="List all product batches",
    description="Retrieve all product batches currently stored in the database.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PRODUCT_BATCHES
)
def read_all_product_batches(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(ProductBatch).order_by(ProductBatch.id.asc())
    return paginate(query, pagination)


# ---------------------------------------------------------------------
# GET ALL PRODUCT BATCHES WITH DETAILS
# ---------------------------------------------------------------------
@router.get(
    "/details",
    response_model=PaginatedResponse[ProductBatchDetailsResponse],
    summary="List all product batches with details",
    description="Retrieve all product batches with detailed information including associated product data.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PRODUCT_BATCHES
)
def read_all_product_batches_with_details(db: db_dependency, pagination: PaginationParams = Depends()):
    query = (
        db.query(ProductBatch)
        .options(joinedload(ProductBatch.product))
        .order_by(ProductBatch.id.asc())
    )
    return paginate(query, pagination)


# ---------------------------------------------------------------------
# GET PRODUCT BATCH BY ID
# ---------------------------------------------------------------------
@router.get(
    "/{product_batch_id}",
    response_model=ProductBatchDetailsResponse,
    summary="Get product batch details",
    description="Retrieve detailed information about a specific product batch by its ID.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PRODUCT_BATCHES
)
def get_product_batch_details(product_batch_id: int, db: db_dependency):
    product_batch = (
        db.query(ProductBatch)
        .options(joinedload(ProductBatch.product))
        .filter(ProductBatch.id == product_batch_id)
        .first()
    )

    if not product_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product batch not found."
        )

    return product_batch


# ---------------------------------------------------------------------
# CREATE PRODUCT BATCH
# ---------------------------------------------------------------------
@router.post(
    "",
    response_model=ProductBatchResponse,
    summary="Create a new product batch",
    description="Create a new product batch with the provided details.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_PRODUCT_BATCHES
)
def create_product_batch(product_batch: ProductBatchCreate, db: db_dependency):
    existing_product = db.query(Product).filter(Product.id == product_batch.product_id).first()

    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with the given ID does not exist."
        )

    existing_batch = db.query(ProductBatch) \
        .filter(
        ProductBatch.product_id == product_batch.product_id,
        ProductBatch.lot_code == product_batch.lot_code
    ).first()

    if existing_batch:
        raise HTTPException(
            status_code=400,
            detail="A batch with this lot_code already exists for this product."
        )

    new_product_batch = ProductBatch(**product_batch.model_dump())
    db.add(new_product_batch)
    db.commit()
    db.refresh(new_product_batch)

    return new_product_batch


# ---------------------------------------------------------------------
# UPDATE PRODUCT BATCH
# ---------------------------------------------------------------------
@router.put(
    "/{product_batch_id}",
    response_model=ProductBatchResponse,
    summary="Update an existing product batch",
    description="Update an existing product batch. Allows partial updates (only send fields you want to modify).",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_PRODUCT_BATCHES
)
def update_product_batch(product_batch_id: int, payload: ProductBatchUpdate, db: db_dependency):

    existing_product_batch = db.get(ProductBatch, product_batch_id)
    if not existing_product_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product batch not found."
        )

    update_data = payload.model_dump(exclude_unset=True)

    final_product_id = update_data.get("product_id", existing_product_batch.product_id)
    final_lot_code = update_data.get("lot_code", existing_product_batch.lot_code)

    if final_lot_code is not None:
        duplicate = (
            db.query(ProductBatch)
            .filter(
                ProductBatch.product_id == final_product_id,
                ProductBatch.lot_code == final_lot_code,
                ProductBatch.id != product_batch_id
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A batch with this lot_code already exists for this product."
            )

    for key, value in update_data.items():
        setattr(existing_product_batch, key, value)

    db.commit()
    db.refresh(existing_product_batch)

    return existing_product_batch


# ---------------------------------------------------------------------
# DELETE PRODUCT BATCH
# ---------------------------------------------------------------------
@router.delete(
    "/{product_batch_id}",
    summary="Delete a product batch",
    description="Delete an existing product batch by its ID.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=CAN_DELETE_PRODUCT_BATCHES
)
def delete_product_batch(product_batch_id: int, db: db_dependency):
    existing_product_batch = db.query(ProductBatch).filter(ProductBatch.id == product_batch_id).first()

    if not existing_product_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product batch not found."
        )

    db.delete(existing_product_batch)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)