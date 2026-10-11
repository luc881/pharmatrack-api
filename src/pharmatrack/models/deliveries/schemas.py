from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DeliveryKind = Literal["sale", "trade"]
DeliveryStatus = Literal["pending", "delivered", "cancelled"]
PaymentMethod = Literal["cash", "transfer", "other"]


class GivenItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(1, ge=1, le=100000)
    animal_id: Optional[int] = Field(None, gt=0)

    model_config = ConfigDict(extra="forbid")


class ReceivedItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(1, ge=1, le=100000)

    model_config = ConfigDict(extra="forbid")


class DeliveryCreate(BaseModel):
    kind: DeliveryKind = "sale"
    status: DeliveryStatus = "pending"
    buyer_name: str = Field(..., min_length=1, max_length=150)
    buyer_contact: Optional[str] = Field(None, max_length=150)
    scheduled_date: date
    scheduled_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    place: Optional[str] = Field(None, max_length=200)
    items_given: list[GivenItem] = Field(default_factory=list, max_length=50)
    items_received: list[ReceivedItem] = Field(default_factory=list, max_length=50)
    amount: Optional[Decimal] = Field(None, ge=0, le=10_000_000, decimal_places=2)
    paid: bool = False
    payment_method: Optional[PaymentMethod] = None
    sale_id: Optional[int] = Field(None, gt=0)
    order_id: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=4000)

    model_config = ConfigDict(extra="forbid")


# PUT reemplaza la entrega completa
DeliveryUpdate = DeliveryCreate


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus

    model_config = ConfigDict(extra="forbid")


class DeliveryResponse(BaseModel):
    id: int
    kind: str
    status: str
    buyer_name: str
    buyer_contact: Optional[str] = None
    scheduled_date: date
    scheduled_time: Optional[str] = None
    place: Optional[str] = None
    items_given: list[dict] = []
    items_received: list[dict] = []
    amount: Optional[Decimal] = None
    paid: bool = False
    payment_method: Optional[str] = None
    sale_id: Optional[int] = None
    order_id: Optional[int] = None
    notes: Optional[str] = None
    delivered_at: Optional[datetime] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
