from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import get_db
from ...models.sale_batch_usage.orm import SaleBatchUsage
from ...models.sale_batch_usage.schemas import (
    SaleBatchUsageResponse,
    SaleBatchUsageDetailsResponse,
)
from ...utils.permissions import (
    CAN_READ_SALE_BATCH_USAGES,
)

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/sale-batch-usages",
    tags=["Sale Batch Usages"],
)


# =========================================================
# GET /
# =========================================================
@router.get(
    "/",
    response_model=List[SaleBatchUsageResponse],
    summary="List all sale-batch usages",
    description="Retrieve all records linking sale details with product batches.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALE_BATCH_USAGES,
)
async def read_all(db: db_dependency):
    return db.query(SaleBatchUsage).all()


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