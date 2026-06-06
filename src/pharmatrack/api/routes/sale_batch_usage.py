from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated, List, Optional
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import get_db
from ...models.sale_batch_usage.orm import SaleBatchUsage
from ...models.sale_batch_usage.schemas import (
    SaleBatchUsageCreate,
    SaleBatchUsageResponse,
    SaleBatchUsageDetailsResponse,
)
from ...models.sale_details.orm import SaleDetail
from ...models.product_batch.orm import ProductBatch
from ...utils.permissions import (
    CAN_READ_SALE_BATCH_USAGES,
    CAN_CREATE_SALE_BATCH_USAGES,
    CAN_DELETE_SALE_BATCH_USAGES,
)
from ...utils.rate_limit import limiter, LIMIT_WRITE

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/sale-batch-usages",
    tags=["Sale Batch Usages"],
)


# =========================================================
# GET /
# =========================================================
@router.get(
    "",
    response_model=List[SaleBatchUsageResponse],
    summary="List all sale-batch usages",
    description="Retrieve all records linking sale details with product batches. Filter by sale_id to get all usages for a specific sale.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALE_BATCH_USAGES,
)
async def read_all(db: db_dependency, sale_id: Optional[int] = None):
    query = db.query(SaleBatchUsage)
    if sale_id is not None:
        query = (
            query
            .join(SaleDetail, SaleBatchUsage.sale_detail_id == SaleDetail.id)
            .filter(SaleDetail.sale_id == sale_id)
        )
    return query.all()


# =========================================================
# GET /{usage_id}
# =========================================================
@router.get(
    "/{usage_id}",
    response_model=SaleBatchUsageDetailsResponse,
    summary="Get sale-batch usage details",
    description="Retrieve a single sale-batch usage record with batch and sale detail info.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALE_BATCH_USAGES,
)
async def read_by_id(usage_id: int, db: db_dependency):
    usage = (
        db.query(SaleBatchUsage)
        .options(
            joinedload(SaleBatchUsage.batch),
            joinedload(SaleBatchUsage.sale_detail),
        )
        .filter(SaleBatchUsage.id == usage_id)
        .first()
    )
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale batch usage not found",
        )
    return usage


# =========================================================
# POST /
# =========================================================
@router.post(
    "",
    response_model=SaleBatchUsageResponse,
    summary="Create a sale-batch usage",
    description="Register which batch was used for a sale detail line. Stock is deducted when the sale is completed.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALE_BATCH_USAGES,
)
@limiter.limit(LIMIT_WRITE)
async def create(request: Request, payload: SaleBatchUsageCreate, db: db_dependency):
    if not db.get(SaleDetail, payload.sale_detail_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale detail {payload.sale_detail_id} not found",
        )
    if not db.get(ProductBatch, payload.batch_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product batch {payload.batch_id} not found",
        )
    usage = SaleBatchUsage(**payload.model_dump())
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


# =========================================================
# DELETE /{usage_id}
# =========================================================
@router.delete(
    "/{usage_id}",
    summary="Delete a sale-batch usage",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=CAN_DELETE_SALE_BATCH_USAGES,
)
@limiter.limit(LIMIT_WRITE)
async def delete(request: Request, usage_id: int, db: db_dependency):
    usage = db.get(SaleBatchUsage, usage_id)
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale batch usage not found",
        )
    db.delete(usage)
    db.commit()
