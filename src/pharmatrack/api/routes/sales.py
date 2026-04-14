from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from ...db.session import get_db
from starlette import status

from ...models.sales.orm import Sale
from ...models.users.orm import User
from ...models.branches.orm import Branch
from ...models.sales.schemas import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    SaleSearchParams,
    PaginatedResponse,
    PaginationParams,
)
from ...utils.permissions import (
    CAN_READ_SALES, CAN_CREATE_SALES, CAN_UPDATE_SALES, CAN_DELETE_SALES
)
from pharmatrack.utils.pagination import paginate
from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
from pharmatrack.utils.sales_calculations import recalc_sale_totals
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE, LIMIT_SEARCH
from ...utils.logger import get_logger

logger = get_logger(__name__)

db_dependency = Annotated[Session, Depends(get_db)]

VALID_SALE_STATUS = ["draft", "completed", "cancelled", "refunded", "partially_refunded"]

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


# =========================================================
# GET /
# =========================================================
@router.get(
    "",
    response_model=PaginatedResponse[SaleResponse],
    summary="List all sales",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
async def read_all(request: Request, db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(Sale).order_by(Sale.date_sale.desc())
    return paginate(query, pagination)


# =========================================================
# GET /search
# =========================================================
@router.get(
    "/search",
    response_model=PaginatedResponse[SaleResponse],
    summary="Search and filter sales",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_SEARCH)
async def search_sales(
    request: Request,
    db: db_dependency,
    params: SaleSearchParams = Depends(),
    pagination: PaginationParams = Depends(),
):
    query = db.query(Sale)

    if params.user_id:
        query = query.filter(Sale.user_id == params.user_id)
    if params.branch_id:
        query = query.filter(Sale.branch_id == params.branch_id)
    if params.status:
        query = query.filter(Sale.status == params.status)
    if params.date_from:
        query = query.filter(Sale.date_sale >= params.date_from)
    if params.date_to:
        query = query.filter(Sale.date_sale <= params.date_to)

    return paginate(query.order_by(Sale.date_sale.desc()), pagination)


# =========================================================
# GET /{sale_id}
# =========================================================
@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get sale by ID",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
async def read_by_id(sale_id: int, db: db_dependency):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")
    return sale


# =========================================================
# POST /
# =========================================================
@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALES,
)
@limiter.limit(LIMIT_WRITE)
async def create(request: Request, sale: SaleCreate, db: db_dependency):
    if not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    new_sale = Sale(
        user_id=sale.user_id,
        branch_id=sale.branch_id,
        description=sale.description,
        status="draft",
        subtotal=0,
        tax=0,
        discount=0,
        total=0,
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    logger.info("Sale created id=%s user_id=%s branch_id=%s", new_sale.id, sale.user_id, sale.branch_id)
    return new_sale


# =========================================================
# POST /{sale_id}/complete
# =========================================================
@router.post(
    "/{sale_id}/complete",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
def complete_sale(sale_id: int, db: db_dependency):
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.sale_details))
        .filter(Sale.id == sale_id)
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    if sale.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft sales can be completed")

    if not sale.sale_details:
        raise HTTPException(status_code=400, detail="Cannot complete an empty sale")

    for detail in sale.sale_details:
        allocate_batches_for_sale_detail(db, detail)

    recalc_sale_totals(db, sale)
    sale.status = "completed"

    db.commit()
    db.refresh(sale)

    logger.info("Sale completed id=%s total=%s", sale.id, sale.total)
    return sale


# =========================================================
# PUT /{sale_id}
# =========================================================
@router.put(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Update a sale",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
async def update(sale_id: int, sale: SaleUpdate, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    if sale.user_id and not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if sale.branch_id and not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    if sale.status and sale.status not in VALID_SALE_STATUS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sale status.")

    if sale.status in ["refunded", "partially_refunded"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund statuses can only be set automatically by the refund system.")

    if existing_sale.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft sales can be modified.")

    for key, value in sale.model_dump(exclude_unset=True).items():
        setattr(existing_sale, key, value)

    db.commit()
    db.refresh(existing_sale)
    logger.info("Sale updated id=%s", sale_id)
    return existing_sale


# =========================================================
# DELETE /{sale_id}
# =========================================================
@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale",
    dependencies=CAN_DELETE_SALES,
)
async def delete(sale_id: int, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    from ...models.refund_products.orm import RefundProduct
    from ...models.sale_details.orm import SaleDetail

    sale_details = db.query(SaleDetail.id).filter(SaleDetail.sale_id == sale_id).all()
    sale_detail_ids = [sd.id for sd in sale_details]

    if sale_detail_ids:
        refund_count = db.query(func.count(RefundProduct.id)).filter(
            RefundProduct.sale_detail_id.in_(sale_detail_ids)
        ).scalar() or 0

        if refund_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a sale that has refunds. Cancel the refunds first.",
            )

    db.delete(existing_sale)
    db.commit()
    logger.info("Sale deleted id=%s", sale_id)
    return