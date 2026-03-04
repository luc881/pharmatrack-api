from slowapi import Limiter
from slowapi.util import get_remote_address
from pharmatrack.config import settings


# =========================================================
# Limiter global
# En produccion aplica los limites; en desarrollo/testing
# se deshabilita para no interferir con los tests.
# =========================================================
limiter = Limiter(
    key_func=get_remote_address,
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