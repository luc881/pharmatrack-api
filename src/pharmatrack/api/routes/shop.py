"""Cuentas de cliente y pedidos del sitio público.

Dos routers:
  - /shop  → lo que consume el sitio público con el token del cliente
  - /orders → lo que consume el dashboard con permisos de staff

Un pedido es una SOLICITUD, no una venta: no toca stock, lotes ni corte de
caja. Cuando lo confirmas, registras la venta en el POS como siempre.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import Depends, APIRouter, HTTPException, Request
from sqlalchemy.orm import selectinload
from starlette import status

from ...config import settings
from ...db.session import db_dependency
from ...models.animals.orm import Animal, Morph, Species, animal_has_morphs
from ...models.customers.orm import ORDER_STATUSES, Order, Customer, OrderItem
from ...models.customers.schemas import (
    OrderCreate,
    GoogleSignIn,
    OrderResponse,
    CustomerUpdate,
    CustomerSession,
    CustomerResponse,
    CheckoutSession,
    OrderAdminResponse,
    OrderStatusUpdate,
)
from ...models.products.orm import Product
from ...utils.email import send_order_emails, send_order_paid_email
from ...utils.google_auth import verify_google_id_token
from ...utils.mercadopago import (
    get_payment,
    valid_signature,
    create_preference,
    find_approved_payment,
)
from ...utils.logger import get_logger
from ...utils.pagination import paginate, PaginationParams, PaginatedResponse
from ...utils.permissions import CAN_READ_ORDERS, CAN_UPDATE_ORDERS
from ...utils.rate_limit import limiter, LIMIT_AUTH
from ...utils.security import create_customer_token, customer_dependency
from .animal_taxonomy import hidden_group_ids

logger = get_logger(__name__)

router = APIRouter(prefix="/shop", tags=["Shop"])
orders_router = APIRouter(prefix="/orders", tags=["Orders"])


# =========================================================
# Login con Google
# =========================================================
@router.post("/auth/google", response_model=CustomerSession,
             summary="Public: iniciar sesion de cliente con Google")
@limiter.limit(LIMIT_AUTH)
async def sign_in_with_google(request: Request, body: GoogleSignIn, db: db_dependency):
    info = verify_google_id_token(body.id_token)

    customer = db.query(Customer).filter(Customer.email == info["email"]).first()
    if customer is None:
        customer = Customer(email=info["email"])
        db.add(customer)
    # El perfil de Google manda sobre el guardado (nombre/foto pueden cambiar);
    # telefono y direccion son del cliente y no se tocan aqui.
    customer.google_sub = info["sub"]
    customer.name = info["name"] or customer.name
    customer.avatar = info["picture"] or customer.avatar
    db.commit()
    db.refresh(customer)

    return {
        "access_token": create_customer_token(customer.id, customer.email),
        "customer": customer,
    }


def _current_customer(db, token_data: dict) -> Customer:
    customer = db.get(Customer, token_data["id"])
    if customer is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication")
    return customer


# =========================================================
# Perfil, favoritos y carrito
# =========================================================
@router.get("/me", response_model=CustomerResponse, summary="Public: mi cuenta")
async def read_me(db: db_dependency, token_data: customer_dependency):
    return _current_customer(db, token_data)


@router.put("/me", response_model=CustomerResponse, summary="Public: guardar mi cuenta")
async def update_me(body: CustomerUpdate, db: db_dependency, token_data: customer_dependency):
    customer = _current_customer(db, token_data)
    # exclude_unset: el sitio manda solo lo que cambio (favoritos, carrito o perfil)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


# =========================================================
# Precio del pedido: SIEMPRE del catalogo, nunca del cliente
# =========================================================
# Llaves del carrito del sitio: "pr-12" (producto), "m3-6" / "s7-u" (animal,
# con escala de precio o "u" de unidad suelta)
_ITEM_RE = re.compile(r"^(?:pr-(?P<product>\d+)|(?P<kind>[ms])(?P<id>\d+)-(?P<tier>\d+|u))$")


def _unavailable(title: str):
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{title} ya no esta disponible.",
    )


def _resolve_product(db, product_id: int) -> dict:
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.is_active.is_(True),
            Product.show_online.is_(True),
            Product.deleted_at.is_(None),
        )
        .first()
    )
    if product is None:
        raise _unavailable("Un producto del pedido")
    return {
        "title": product.title,
        "detail": None,
        "unit_price": product.price_retail,
        # granel: la cantidad son gramos y el precio es por gramo
        "unit": None if product.is_unit_sale else product.unit_name,
    }


def _listing_animals(db, species_id: int, morph_id: Optional[int]):
    """Ejemplares disponibles del listado, igual que agrupa el sitio:
    por morph, o los que no tienen morph cuando el listado es de especie."""
    query = db.query(Animal).filter(
        Animal.species_id == species_id, Animal.status == "available"
    )
    if morph_id is not None:
        return query.join(animal_has_morphs).filter(
            animal_has_morphs.c.morph_id == morph_id
        ).all()
    return [a for a in query.all() if not a.morphs]


def _resolve_animal(db, kind: str, entity_id: int, tier: str) -> dict:
    morph = db.get(Morph, entity_id) if kind == "m" else None
    species = morph.species if morph else db.get(Species, entity_id)
    if species is None or (kind == "m" and morph is None):
        raise _unavailable("Un articulo del pedido")

    # Un grupo oculto no se puede pedir aunque alguien conserve la llave
    group_id = species.genus.group_id if species.genus else None
    if group_id is not None and group_id in hidden_group_ids(db):
        raise _unavailable("Un articulo del pedido")

    base = species.common_name or " ".join(
        filter(None, [species.genus.name if species.genus else None, species.name])
    )
    title = f"{base} {morph.name}" if morph else base

    if tier != "u":
        quantity = int(tier)
        match = next(
            (t for t in (species.price_tiers or []) if int(t.get("quantity", 0)) == quantity),
            None,
        )
        if match is None:
            raise _unavailable(title)
        return {
            "title": title,
            "detail": f"Paquete de {quantity}",
            "unit_price": Decimal(str(match["price"])),
            "unit": None,
        }

    animals = _listing_animals(db, species.id, morph.id if morph else None)
    if not animals:
        raise _unavailable(title)
    return {
        "title": title,
        "detail": None,
        # el sitio muestra "desde X"; el pedido se toma con ese mismo precio
        "unit_price": min(a.price for a in animals),
        "unit": None,
    }


def resolve_item(db, key: str) -> dict:
    match = _ITEM_RE.match(key)
    if not match:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Articulo desconocido: {key}")
    if match.group("product"):
        return _resolve_product(db, int(match.group("product")))
    return _resolve_animal(db, match.group("kind"), int(match.group("id")), match.group("tier"))


# =========================================================
# Pedidos del cliente
# =========================================================
@router.get("/orders", response_model=list[OrderResponse], summary="Public: mis pedidos")
async def list_my_orders(db: db_dependency, token_data: customer_dependency):
    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == token_data["id"])
        .order_by(Order.id.desc())
        .all()
    )


# Anti-spam de pedidos (por cliente, no por IP):
#  - tope de pedidos pendientes: mientras no atiendas los que tiene, no puede
#    seguir metiendo más (y el mensaje le explica qué hacer)
#  - pedido idéntico a uno pendiente = duplicado por confusión, se rechaza
#    diciéndole el folio que ya tiene
#  - tope diario de creación (cuenta también los cancelados): sin esto, el
#    bucle crear→cancelar→crear brincaría el tope de pendientes y cada
#    creación te manda un correo
MAX_PENDING_ORDERS = 3
MAX_ORDERS_PER_DAY = 10


def _reject_order_flood(db, customer_id: int, items) -> None:
    created_today = (
        db.query(Order)
        .filter(Order.customer_id == customer_id,
                # created_at es naive-UTC en la BD (Postgres corre en UTC)
                Order.created_at >= datetime.now(timezone.utc).replace(tzinfo=None)
                - timedelta(hours=24))
        .count()
    )
    if created_today >= MAX_ORDERS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Has hecho demasiados pedidos en las últimas 24 horas. "
                   "Escríbenos por WhatsApp y te ayudamos directo.",
        )

    pending = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer_id, Order.status == "pending")
        .all()
    )
    wanted = sorted((line.key, float(line.qty)) for line in items)
    for existing in pending:
        if sorted((i.item_key, float(i.quantity)) for i in existing.items) == wanted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Este pedido es idéntico a tu pedido {existing.code}, que sigue "
                       "pendiente. Puedes verlo en «Mis pedidos».",
            )
    if len(pending) >= MAX_PENDING_ORDERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya tienes {len(pending)} pedidos pendientes. Espera a que los "
                   "confirmemos (o escríbenos por WhatsApp) antes de hacer otro.",
        )


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED,
             summary="Public: hacer un pedido")
@limiter.limit("5/minute")
async def create_order(request: Request, body: OrderCreate, db: db_dependency,
                       token_data: customer_dependency):
    customer = _current_customer(db, token_data)
    _reject_order_flood(db, customer.id, body.items)

    order = Order(
        # mismo formato que el code de animales; uuid evita colisiones sin ciclo de reintento
        code=f"PD-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        status="pending",
        contact_name=body.contact_name or customer.name,
        contact_phone=body.contact_phone or customer.phone,
        address=body.address or customer.address,
        notes=body.notes,
        delivery_method=body.delivery_method,
    )

    total = Decimal("0")
    for line in body.items:
        resolved = resolve_item(db, line.key)
        quantity = Decimal(str(line.qty))
        order.items.append(OrderItem(
            item_key=line.key,
            title=resolved["title"],
            detail=resolved["detail"],
            quantity=quantity,
            unit=resolved["unit"],
            unit_price=resolved["unit_price"],
        ))
        total += quantity * resolved["unit_price"]

    order.total = total
    db.add(order)
    db.commit()
    db.refresh(order)

    # El correo nunca tumba el pedido: ya quedo guardado
    try:
        send_order_emails(order, customer, settings.order_notify_email)
    except Exception as exc:  # noqa: BLE001
        logger.error("Order %s saved but email failed: %s", order.id, exc)

    return order


@router.post("/orders/{order_id}/checkout", response_model=CheckoutSession,
             summary="Public: pagar en linea un pedido de entrega personal")
@limiter.limit("10/minute")
async def start_checkout(request: Request, order_id: int, db: db_dependency,
                         token_data: customer_dependency):
    order = db.query(Order).filter(
        Order.id == order_id, Order.customer_id == token_data["id"]
    ).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Este pedido ya no está pendiente de pago.")
    if order.delivery_method != "pickup":
        # Con envío el total todavía no es final: se cobra por link de pago
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Los pedidos con envío se cobran una vez cotizado el envío; "
                   "te mandamos el link de pago por WhatsApp.",
        )

    notification_url = f"{str(request.base_url).rstrip('/')}/api/v1/shop/payments/webhook"
    _preference_id, payment_url = create_preference(order, notification_url)
    return {"payment_url": payment_url}


def _apply_payment(db, order: Order, payment: dict) -> bool:
    """Acredita un pago ya verificado contra Mercado Pago. Devuelve si cambió
    algo. Mismas reglas para el webhook y para la reconciliación."""
    if not payment or payment.get("status") != "approved":
        return False

    payment_id = str(payment.get("id") or "")
    if not payment_id or order.payment_id == payment_id:
        return False  # idempotente: el mismo aviso llega varias veces

    # Doble pago (dos checkouts abiertos, dos aprobados): se conserva el
    # primero y NO se manda otro correo; el segundo se reembolsa a mano.
    if order.payment_id:
        logger.error("DOBLE PAGO en el pedido %s: ya tenia %s y llego %s — reembolsar el segundo",
                     order.code, order.payment_id, payment_id)
        return False

    # El importe debe cubrir el pedido; si no, se registra y se revisa a mano
    paid = Decimal(str(payment.get("transaction_amount") or 0))
    if paid < order.total:
        logger.error("Pago %s de %s no cubre el pedido %s (%s)",
                     payment_id, paid, order.code, order.total)
        return False

    order.payment_id = payment_id
    order.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if order.status in ("pending", "cancelled"):
        order.status = "paid"
    db.commit()
    logger.info("Pedido %s pagado (payment %s)", order.code, payment_id)

    try:
        send_order_paid_email(order, order.customer, settings.order_notify_email)
    except Exception as exc:  # noqa: BLE001
        logger.error("Order %s paid but email failed: %s", order.code, exc)
    return True


@router.post("/orders/{order_id}/sync-payment", response_model=OrderResponse,
             summary="Public: reconciliar el pago de un pedido")
@limiter.limit("20/minute")
async def sync_order_payment(request: Request, order_id: int, db: db_dependency,
                             token_data: customer_dependency):
    """Lo llama el sitio al volver de Mercado Pago. Red de seguridad por si el
    webhook no llegó: le pregunta a Mercado Pago si hay un pago aprobado para
    este pedido. Los parametros que trae el navegador no se usan para nada."""
    order = db.query(Order).filter(
        Order.id == order_id, Order.customer_id == token_data["id"]
    ).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.payment_id is None and order.code:
        payment = find_approved_payment(order.code)
        if payment:
            _apply_payment(db, order, payment)
            db.refresh(order)
    return order


@router.post("/payments/webhook", summary="Mercado Pago: aviso de pago",
             status_code=status.HTTP_200_OK)
async def mercadopago_webhook(request: Request, db: db_dependency):
    """Público y sin auth (lo llama Mercado Pago). No confía en el cuerpo:
    solo toma el id del pago y lo consulta con nuestro token."""
    # Cuerpo tolerante: un JSON inválido no debe responder 500 (Mercado Pago
    # reintentaría en bucle un mensaje que nunca va a mejorar)
    try:
        body = await request.json() if await request.body() else {}
    except Exception:  # noqa: BLE001
        body = {}
    payment_id = (
        str((body.get("data") or {}).get("id") or "")
        or request.query_params.get("data.id")
        or request.query_params.get("id")
        or ""
    )
    # Siempre 200: si respondemos error, Mercado Pago reintenta en bucle
    if not payment_id:
        return {"received": True}

    # Filtro previo: descarta ruido sin gastar una llamada a Mercado Pago.
    # No es lo que da la seguridad — eso lo hace la consulta de abajo.
    if not valid_signature(
        request.headers.get("x-signature", ""),
        request.headers.get("x-request-id", ""),
        payment_id,
    ):
        logger.warning("Webhook con firma inválida para el pago %s", payment_id)
        return {"received": True}

    payment = get_payment(payment_id)
    if not payment:
        return {"received": True}
    # el id de la consulta manda sobre el del cuerpo
    payment.setdefault("id", payment_id)

    order = db.query(Order).filter(
        Order.code == payment.get("external_reference")
    ).first()
    if order is None:
        logger.warning("Pago %s aprobado sin pedido: ref=%s",
                       payment_id, payment.get("external_reference"))
        return {"received": True}

    _apply_payment(db, order, payment)
    return {"received": True}


@router.delete("/orders/{order_id}", response_model=OrderResponse,
               summary="Public: cancelar mi pedido pendiente")
@limiter.limit("10/minute")
async def cancel_my_order(request: Request, order_id: int, db: db_dependency,
                          token_data: customer_dependency):
    # Sólo el dueño y sólo pendientes: un pedido confirmado ya se está
    # preparando — eso se habla por WhatsApp, no con un botón.
    order = db.query(Order).filter(
        Order.id == order_id, Order.customer_id == token_data["id"]
    ).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.status != "pending":
        detail = ("Este pedido ya está pagado; escríbenos por WhatsApp y lo resolvemos."
                  if order.status == "paid" else
                  "Este pedido ya fue confirmado; escríbenos por WhatsApp para cambiarlo.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


# =========================================================
# Pedidos en el dashboard
# =========================================================
def _admin_payload(order: Order) -> dict:
    return {
        **OrderResponse.model_validate(order).model_dump(),
        "customer_email": order.customer.email if order.customer else None,
        "customer_name": order.customer.name if order.customer else None,
    }


@orders_router.get("", response_model=PaginatedResponse[OrderAdminResponse],
                   dependencies=CAN_READ_ORDERS, summary="Listar pedidos del sitio")
async def list_orders(db: db_dependency, order_status: Optional[str] = None,
                      pagination: PaginationParams = Depends()):
    query = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .order_by(Order.id.desc())
    )
    if order_status:
        query = query.filter(Order.status == order_status)
    page = paginate(query, pagination)
    page["data"] = [_admin_payload(order) for order in page["data"]]
    return page


@orders_router.get("/{order_id}", response_model=OrderAdminResponse,
                   dependencies=CAN_READ_ORDERS, summary="Detalle de un pedido")
async def get_order(order_id: int, db: db_dependency):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return _admin_payload(order)


@orders_router.put("/{order_id}", response_model=OrderAdminResponse,
                   dependencies=CAN_UPDATE_ORDERS, summary="Cambiar el estado de un pedido")
async def update_order_status(order_id: int, body: OrderStatusUpdate, db: db_dependency):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if body.status not in ORDER_STATUSES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Estado invalido.")
    # "Pagado" lo acredita únicamente un pago verificado (webhook o
    # reconciliación); marcarlo a mano diría que hay dinero que no existe
    if body.status == "paid" and not order.payment_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pagado lo asigna el pago en línea. Si te pagaron por otro medio, "
                   "usa Confirmado.",
        )
    order.status = body.status
    db.commit()
    db.refresh(order)
    return _admin_payload(order)
