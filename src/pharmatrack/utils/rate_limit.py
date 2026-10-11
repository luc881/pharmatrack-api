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