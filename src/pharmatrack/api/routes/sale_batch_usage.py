from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.sale_batch_usage.orm import SaleBatchUsage
from ...models.sale_batch_usage.schemas import (
    SaleBatchUsageCreate,
    SaleBatchUsageUpdate,
    SaleBatchUsageResponse
)
from ...models.sale_details.orm import SaleDetail
from ...models.product_batch.orm import ProductBatch
from ...models.permissions.orm import Permission
from ...utils.permissions import CAN_READ_PRODUCTS, CAN_CREATE_PRODUCTS, CAN_UPDATE_PRODUCTS

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/sale-batch-usages",
    tags=["Sale Batch Usages"]
)


@router.get("/",
            response_model=List[SaleBatchUsageResponse],
            summary="List all sale-batch usages",
            description="Retrieve all records linking sale details with product batches.",
            dependencies=CAN_READ_PRODUCTS)
async def read_all(db: db_dependency):
    usages = db.query(SaleBatchUsage).all()
    return usages

