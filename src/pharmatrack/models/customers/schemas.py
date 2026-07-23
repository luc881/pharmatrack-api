from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field, BaseModel, ConfigDict, field_validator

from .orm import DELIVERY_METHODS, ORDER_STATUSES

OrderStatus = Literal[ORDER_STATUSES]  # type: ignore[valid-type]
DeliveryMethod = Literal[DELIVERY_METHODS]  # type: ignore[valid-type]


# =========================================================
# Cliente
# =========================================================

# Campos de direccion, compartidos por lectura y escritura. El texto
# `address` no se manda: lo compone el servidor a partir de estos.
class AddressFields(BaseModel):
    street: Optional[str] = Field(None, max_length=200)
    ext_number: Optional[str] = Field(None, max_length=20)
    int_number: Optional[str] = Field(None, max_length=20)
    neighborhood: Optional[str] = Field(None, max_length=150)
    zip_code: Optional[str] = Field(None, max_length=5)
    city: Optional[str] = Field(None, max_length=150)
    state: Optional[str] = Field(None, max_length=60)
    address_notes: Optional[str] = None

    @field_validator("zip_code")
    @classmethod
    def _five_digits(cls, value):
        if value in (None, ""):
            return None
        value = value.strip()
        if not (value.isdigit() and len(value) == 5):
            raise ValueError("El código postal son 5 dígitos.")
        return value


class CustomerResponse(AddressFields):
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


class CustomerUpdate(AddressFields):
    """Todo opcional: el sitio manda solo lo que cambió (perfil, favoritos o carrito)."""

    name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
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
    # pickup = entrega personal en CDMX (se puede pagar en linea de una vez)
    delivery_method: DeliveryMethod = "shipping"
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
    delivery_method: str = "shipping"
    payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None
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


class CartValidate(BaseModel):
    """Revisión del carrito contra el catálogo: disponibilidad, precio y tope."""

    items: List[OrderItemIn] = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid")


class CartLineStatus(BaseModel):
    key: str
    # False = el artículo ya no se puede pedir (borrado/vendido/oculto)
    available: bool
    title: Optional[str] = None
    detail: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    # Máximo pedible hoy (para paquetes, en paquetes). None = sin tope (productos)
    max_qty: Optional[int] = None


class CartValidateResponse(BaseModel):
    items: List[CartLineStatus]


class CheckoutSession(BaseModel):
    """A donde mandar al cliente para pagar."""

    payment_url: str


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

    model_config = ConfigDict(extra="forbid")
