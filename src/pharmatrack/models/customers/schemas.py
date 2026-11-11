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
    address_notes: Optional[str] = Field(None, max_length=500)

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
    # Acotados: se guardan tal cual en la fila del cliente
    favorites: Optional[List[str]] = Field(None, max_length=500)
    cart: Optional[List[dict]] = Field(None, max_length=200)

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
    # Acotado todo lo que escribe el cliente: se guarda y se manda por correo
    items: List[OrderItemIn] = Field(..., min_length=1, max_length=100)
    # pickup = entrega personal en CDMX (se puede pagar en linea de una vez)
    delivery_method: DeliveryMethod = "shipping"
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=600)
    notes: Optional[str] = Field(None, max_length=1000)

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
    # Guía de envío: el cliente ve paquetería y rastreo
    shipping_carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderAdminResponse(OrderResponse):
    """Igual, más quién lo hizo — solo para el dashboard."""

    customer_id: Optional[int] = None
    customer_blocked: bool = False
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    # Solo el dashboard: el PDF de la guía, lo que costó y la dirección por
    # partes del cliente (para prellenar el destino al cotizar)
    shipping_service: Optional[str] = None
    label_url: Optional[str] = None
    shipping_cost: Optional[float] = None
    customer_address: Optional[dict] = None


class CustomerBlock(BaseModel):
    blocked: bool

    model_config = ConfigDict(extra="forbid")


class ShippingDestination(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    street: str = Field(..., min_length=1, max_length=200)
    number: Optional[str] = Field(None, max_length=20)
    district: Optional[str] = Field(None, max_length=150)
    city: str = Field(..., min_length=1, max_length=150)
    state: str = Field(..., min_length=2, max_length=60)
    postal_code: str = Field(..., pattern=r"^\d{5}$")
    reference: Optional[str] = Field(None, max_length=250)

    model_config = ConfigDict(extra="forbid")


class ShippingPackage(BaseModel):
    content: str = Field(..., min_length=1, max_length=100)
    weight: float = Field(..., gt=0, le=70, description="kg")
    length: float = Field(..., gt=0, le=200, description="cm")
    width: float = Field(..., gt=0, le=200, description="cm")
    height: float = Field(..., gt=0, le=200, description="cm")
    declared_value: float = Field(0, ge=0)

    model_config = ConfigDict(extra="forbid")


class ShippingRateRequest(BaseModel):
    destination: ShippingDestination
    package: ShippingPackage

    model_config = ConfigDict(extra="forbid")


class ShippingLabelRequest(ShippingRateRequest):
    carrier: str = Field(..., min_length=1, max_length=40)
    service: str = Field(..., min_length=1, max_length=60)


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
