"""Checkout Pro de Mercado Pago.

ponytail: dos llamadas HTTP con httpx en vez del SDK oficial — no vale una
dependencia más. Si algún día hacen falta suscripciones o split de pagos,
ahí sí conviene el SDK.

Regla de seguridad: el webhook NUNCA se cree lo que trae en el cuerpo. Solo
se le toma el id del pago y se consulta a Mercado Pago con nuestro token;
lo que diga esa consulta es lo único que marca un pedido como pagado.
"""
import hmac
import hashlib

import httpx
from fastapi import HTTPException
from starlette import status

from pharmatrack.config import settings
from pharmatrack.utils.logger import get_logger

logger = get_logger(__name__)

API = "https://api.mercadopago.com"


def is_configured() -> bool:
    return bool(settings.mercadopago_access_token.strip())


def valid_signature(x_signature: str, x_request_id: str, data_id: str) -> bool:
    """Firma HMAC del webhook (cabecera x-signature).

    Es una capa previa, no la que da seguridad: aunque alguien falsifique una
    firma válida, el pago se sigue verificando contra la API de Mercado Pago.
    Sirve para descartar ruido sin gastar una llamada saliente por petición.

    Sin MERCADOPAGO_WEBHOOK_SECRET configurado devuelve True: el sistema debe
    seguir funcionando si el secreto aún no se ha puesto.
    """
    secret = settings.mercadopago_webhook_secret.strip()
    if not secret:
        return True
    if not x_signature:
        return False

    # x-signature: "ts=1704908010,v1=618c85345248dd820d5fd4..."
    parts = dict(
        piece.split("=", 1) for piece in x_signature.split(",") if "=" in piece
    )
    ts, received = parts.get("ts", "").strip(), parts.get("v1", "").strip()
    if not ts or not received:
        return False

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    # compare_digest: comparación en tiempo constante
    return hmac.compare_digest(expected, received)


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.mercadopago_access_token.strip()}"}


# Mercado Pago ya no marca las credenciales de prueba con un prefijo: tanto
# las de prueba como las productivas empiezan con APP_USR-. Es la credencial
# usada la que decide si el cobro es real, no la URL a la que mandemos.


def create_preference(order, notification_url: str) -> tuple[str, str]:
    """Crea la preferencia de pago. Devuelve (preference_id, url_de_pago).

    Los importes salen del pedido ya guardado, que a su vez los resolvió
    contra el catálogo — nunca de lo que mandó el navegador.
    """
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los pagos en línea no están configurados.",
        )

    back = f"{settings.site_url}/mis-pedidos"
    payload = {
        "items": [
            {
                "title": item.title[:250],
                "description": (item.detail or "")[:250] or None,
                "quantity": int(item.quantity),
                "unit_price": float(item.unit_price),
                "currency_id": "MXN",
            }
            for item in order.items
        ],
        # external_reference es como el webhook encuentra el pedido después
        "external_reference": order.code,
        "notification_url": notification_url,
        "back_urls": {"success": back, "failure": back, "pending": back},
        "auto_return": "approved",
        "statement_descriptor": "OPUNTIA DEN",
    }

    try:
        res = httpx.post(f"{API}/checkout/preferences", json=payload,
                         headers=_headers(), timeout=15)
    except httpx.HTTPError as exc:
        logger.error("Mercado Pago unreachable: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="No se pudo contactar a Mercado Pago.") from exc

    if res.status_code >= 300:
        logger.error("Mercado Pago preference failed %s: %s", res.status_code, res.text[:500])
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="No se pudo iniciar el pago.")

    data = res.json()
    # init_point sirve para ambos ambientes; sandbox_init_point solo queda de
    # respaldo para respuestas viejas que no traigan init_point
    url = data.get("init_point") or data.get("sandbox_init_point")
    if not url:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="No se pudo iniciar el pago.")
    return data["id"], url


def find_approved_payment(external_reference: str) -> dict | None:
    """Busca un pago aprobado por la referencia del pedido.

    Red de seguridad para cuando el webhook no llega (deploy a media
    transacción, timeout, caída): sin esto el cliente paga y su pedido se
    queda 'pendiente' para siempre.
    """
    if not is_configured():
        return None
    try:
        res = httpx.get(f"{API}/v1/payments/search",
                        params={"external_reference": external_reference},
                        headers=_headers(), timeout=15)
    except httpx.HTTPError as exc:
        logger.error("Mercado Pago unreachable on search %s: %s", external_reference, exc)
        return None
    if res.status_code != 200:
        return None
    for payment in res.json().get("results", []):
        if payment.get("status") == "approved":
            return payment
    return None


def get_payment(payment_id: str) -> dict | None:
    """Consulta un pago. None si no existe o no es nuestro."""
    if not is_configured():
        return None
    try:
        res = httpx.get(f"{API}/v1/payments/{payment_id}", headers=_headers(), timeout=15)
    except httpx.HTTPError as exc:
        logger.error("Mercado Pago unreachable on payment %s: %s", payment_id, exc)
        return None
    if res.status_code != 200:
        logger.warning("Payment %s lookup returned %s", payment_id, res.status_code)
        return None
    return res.json()
