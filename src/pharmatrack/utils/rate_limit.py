from slowapi import Limiter
from slowapi.util import get_remote_address


# =========================================================
# 🔹 Limiter global
# get_remote_address obtiene la IP del cliente automáticamente
# =========================================================
limiter = Limiter(key_func=get_remote_address)


# =========================================================
# 🔹 Límites predefinidos por tipo de endpoint
# =========================================================

# Autenticación — el más estricto, evita fuerza bruta
LIMIT_AUTH         = "5/minute"

# Escritura — creación, actualización, eliminación
LIMIT_WRITE        = "30/minute"

# Lectura general
LIMIT_READ         = "60/minute"

# Búsquedas y listados paginados
LIMIT_SEARCH       = "40/minute"