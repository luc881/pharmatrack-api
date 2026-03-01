from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging

from .config import settings
from .logging_config import setup_logging

# ✅ Debe llamarse ANTES de importar los routers
setup_logging()

from .api.v1 import api_v1_router
from .utils.rate_limit import limiter

# =========================================================
# 🔹 Logger
# =========================================================
logger = logging.getLogger(__name__)


# =========================================================
# 🔹 Metadata de tags — organiza el Swagger por secciones
# =========================================================
tags_metadata = [
    {
        "name": "Auth",
        "description": "Autenticación con JWT. Login, renovación de token y logout.",
    },
    {
        "name": "Users",
        "description": "Gestión de usuarios del sistema (farmacéuticos, cajeros, admins).",
    },
    {
        "name": "Roles",
        "description": "Roles de acceso asignables a usuarios.",
    },
    {
        "name": "Permissions",
        "description": "Permisos granulares asignables a roles.",
    },
    {
        "name": "Branches",
        "description": "Sucursales de la farmacia.",
    },
    {
        "name": "Products",
        "description": "Catálogo de productos. Incluye precios, stock, ingredientes y lotes.",
    },
    {
        "name": "Products Brand",
        "description": "Marcas de los productos.",
    },
    {
        "name": "Products Master",
        "description": "Productos genéricos o maestros que agrupan variantes.",
    },
    {
        "name": "Products Categories",
        "description": "Categorías jerárquicas de productos (árbol padre-hijo).",
    },
    {
        "name": "Products Batches",
        "description": "Lotes de productos con fecha de caducidad, stock y costo.",
    },
    {
        "name": "Ingredients",
        "description": "Ingredientes activos asociados a productos.",
    },
    {
        "name": "Sales",
        "description": "Ventas. Flujo: draft → completar → pagos. Soporta devoluciones.",
    },
    {
        "name": "Sale Details",
        "description": "Líneas de detalle de cada venta (productos, cantidades, precios).",
    },
    {
        "name": "Sale Payments",
        "description": "Pagos asociados a ventas (efectivo, tarjeta, etc).",
    },
    {
        "name": "Refund Products",
        "description": "Devoluciones de productos de ventas completadas.",
    },
    {
        "name": "Suppliers",
        "description": "Proveedores de productos.",
    },
    {
        "name": "Purchases",
        "description": "Órdenes de compra a proveedores.",
    },
    {
        "name": "Health Check",
        "description": "Estado del servidor.",
    },
]


# =========================================================
# 🔹 Lifespan
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🌱 Running database seeds...")
    from .seeds.init_db import init_db
    init_db()
    yield
    logger.info("🛑 Application shutdown")


# =========================================================
# 🔹 App
# =========================================================
app = FastAPI(
    title="POS System API",
    description="""
## Sistema de Punto de Venta para Farmacia

API REST para la gestión completa de inventario, ventas y operaciones de una farmacia.

### Funcionalidades principales

- 🔐 **Autenticación** con JWT y refresh tokens
- 👥 **Control de acceso** por roles y permisos granulares
- 💊 **Inventario** con lotes, fechas de caducidad y trazabilidad
- 🛒 **Ventas** con flujo draft → completar, pagos y devoluciones
- 📦 **Compras** a proveedores con seguimiento de stock
- 🌿 **Ingredientes activos** asociados a productos
- 🏪 **Multisucursal** con control por branch

### Autenticación

Todos los endpoints (excepto `/auth/token`) requieren un token JWT en el header:

```
Authorization: Bearer <token>
```

Obtén tu token en **POST /api/v1/auth/token**.
    """,
    version="1.0.0",
    contact={
        "name": "POS System",
    },
    license_info={
        "name": "Proyecto académico — Opción a titulación",
    },
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Registrar el limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =========================================================
# 🔹 CORS
# =========================================================
if settings.is_production:
    allowed_origins = settings.allowed_origins
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 🔹 Manejo global de excepciones
# =========================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled error on {request.method} {request.url}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# =========================================================
# 🔹 Endpoints base (fuera del versionado)
# =========================================================
@app.get("/", tags=["Health Check"])
def root():
    return {
        "message": "POS System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/healthcheck", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is running"}


# =========================================================
# 🔹 Router versionado
# =========================================================
app.include_router(api_v1_router)