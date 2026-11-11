import hmac

from jose import jwt, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from pharmatrack.config import settings


def client_ip(request: Request) -> str:
    """IP real del cliente detrás del proxy de Railway.

    Railway documenta X-Real-IP como la IP del cliente y la pone su edge.
    X-Forwarded-For no sirve: uvicorn (--forwarded-allow-ips "*") toma el
    primer valor, que el cliente puede inventar para saltarse los límites.
    Sin X-Real-IP (local, tests) se usa la IP de la conexión.
    """
    real = request.headers.get("x-real-ip", "").strip()
    return real or get_remote_address(request)


def shop_client_ip(request: Request) -> str:
    """IP del visitante de la tienda.

    El sitio público llama a la API desde su servidor, así que X-Real-IP es la
    de ese servidor, igual para todos los clientes. El sitio manda la IP del
    visitante en X-Client-IP, y solo se le cree si trae el secreto compartido.
    """
    secret = settings.shop_proxy_secret.strip()
    sent = request.headers.get("x-proxy-secret", "")
    forwarded = request.headers.get("x-client-ip", "").strip()
    if secret and forwarded and hmac.compare_digest(sent.encode(), secret.encode()):
        return forwarded
    return client_ip(request)


def trusted_shop_ip(request: Request) -> str | None:
    """La IP del visitante solo cuando viene avalada por el sitio; si no, None."""
    ip = shop_client_ip(request)
    return ip if ip != client_ip(request) else None


def customer_key(request: Request) -> str:
    """Límite por cuenta de cliente (su token); sin token válido, por IP.
    Así el exceso de un cliente no le cierra la puerta a los demás."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            payload = jwt.decode(auth[7:], settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("id") is not None:
                return f"customer:{payload['id']}"
        except JWTError:
            pass
    return shop_client_ip(request)


# =========================================================
# Limiter global
# En produccion aplica los limites; en desarrollo/testing
# se deshabilita para no interferir con los tests.
# =========================================================
# ponytail: memoria por proceso; con --workers 2 cada límite rinde el doble.
# Redis (storage_uri) si hiciera falta un límite exacto.
limiter = Limiter(
    key_func=client_ip,
    enabled=settings.is_production,
)


# =========================================================
# Limites predefinidos por tipo de endpoint
# =========================================================

# Autenticacion — el mas estricto, evita fuerza bruta
LIMIT_AUTH   = "5/minute"

# Escritura — creacion, actualizacion, eliminacion
LIMIT_WRITE  = "30/minute"

# Lectura general
LIMIT_READ   = "60/minute"

# Busquedas y listados paginados
LIMIT_SEARCH = "40/minute"