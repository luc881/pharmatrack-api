from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field, BaseModel, ConfigDict, field_validator

from .orm import ORDER_STATUSES

OrderStatus = Literal[ORDER_STATUSES]  # type: ignore[valid-type]


# =========================================================
# Cliente
# =========================================================
class CustomerResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    favorites: List[str] = Field(default_factory=list)
    cart: List[dict] = Field(default_factory=list)

    # En la BD son NULL mientras el cliente no guarde nada; el sitio siempre
    # espera listas.
    @field_validator("favorites", "cart", mode="before")
    @classmethod
    def _none_is_empty(cls, value):
        return value or []

    model_config = ConfigDict(from_attributes=True)


class CustomerUpdate(BaseModel):
    """Todo opcional: el sitio manda solo lo que cambió (perfil, favoritos o carrito)."""

    name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    favorites: Optional[List[str]] = None
    cart: Optional[List[dict]] = None

    model_config = ConfigDict(extra="forbid")


class GoogleSignIn(BaseModel):
    id_token: str


class CustomerSession(BaseModel):
    access_token: str
    customer: CustomerResponse


# =========================================================
# Pedidos
# =========================================================
class OrderItemIn(BaseModel):
    """Lo que manda el sitio. El precio NO viene de aquí: lo resuelve el
    servidor contra el catálogo (si no, cualquiera pediría a $1)."""

    key: str = Field(..., max_length=40)
    qty: float = Field(..., gt=0, le=100_000)

    model_config = ConfigDict(extra="ignore")


class OrderCreate(BaseModel):
    items: List[OrderItemIn] = Field(..., min_length=1)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class OrderItemResponse(BaseModel):
    id: int
    item_key: str
    title: str
    detail: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    code: Optional[str] = None
    status: str
    total: float
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderAdminResponse(OrderResponse):
    """Igual, más quién lo hizo — solo para el dashboard."""

    customer_email: Optional[str] = None
    customer_name: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

    model_config = ConfigDict(extra="forbid")
