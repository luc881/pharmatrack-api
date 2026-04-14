from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from ...db.session import get_db
from ...models.product_batch.orm import ProductBatch
from ...models.products.orm import Product
from ...utils.permissions import CAN_READ_PRODUCT_BATCHES
from ...utils.rate_limit import limiter, LIMIT_READ

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/calendar", tags=["Calendar"])


def _batch_color(expiration_date: date) -> str:
    diff = (expiration_date - date.today()).days
    if diff < 0:    return "#B71D18"
    if diff <= 7:   return "#FF5630"
    if diff <= 30:  return "#FFAB00"
    return "#22C55E"


class CalendarEvent(BaseModel):
    id: str
    title: str
    start: date
    end: date
    allDay: bool = True
    color: str
    textColor: str = "#fff"


@router.get(
    "/events",
    response_model=list[CalendarEvent],
    summary="Batch expiration calendar events",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_PRODUCT_BATCHES,
)
@limiter.limit(LIMIT_READ)
async def get_calendar_events(
    request: Request,
    db: db_dependency,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    range_start = start or date.today()
    range_end = end or (date.today() + timedelta(days=365))

    rows = (
        db.query(ProductBatch, Product.title)
        .join(Product, Product.id == ProductBatch.product_id)
        .filter(
            ProductBatch.expiration_date.isnot(None),
            ProductBatch.expiration_date >= range_start,
            ProductBatch.expiration_date <= range_end,
        )
        .order_by(ProductBatch.expiration_date.asc())
        .all()
    )

    return [
        CalendarEvent(
            id=str(batch.id),
            title=f"{title} ({batch.lot_code})" if batch.lot_code else title,
            start=batch.expiration_date,
            end=batch.expiration_date,
            color=_batch_color(batch.expiration_date),
        )
        for batch, title in rows
    ]
