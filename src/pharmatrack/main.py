from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .api.v1 import api_v1_router
from .config import settings
from .utils.logger import get_logger
logger = get_logger(__name__)
from slowapi import _rate_limit_exceeded_handler
from .utils.rate_limit import limiter

tags_metadata = [
    {"name": "Auth",               "description": "Login, refresh token y logout."},
    {"name": "Users",              "description": "Gestion de usuarios del sistema."},
    {"name": "Roles",              "description": "Roles y asignacion de permisos."},
    {"name": "Permissions",        "description": "Catalogo de permisos disponibles."},
    {"name": "Branches",           "description": "Sucursales de la farmacia."},
    {"name": "Ingredients",        "description": "Ingredientes activos de productos."},
    {"name": "Product Brands",     "description": "Marcas de productos."},
    {"name": "Products",           "description": "Catalogo de productos."},
    {"name": "Product Batches",    "description": "Lotes con fecha de caducidad y stock."},
    {"name": "Product Master",     "description": "Productos genericos (maestros)."},
    {"name": "Product Categories", "description": "Arbol jerarquico de categorias."},
    {"name": "Sales",              "description": "Ventas (flujo draft -> completed)."},
    {"name": "Sale Details",       "description": "Lineas de detalle de venta."},
    {"name": "Sale Payments",      "description": "Pagos asociados a ventas."},
    {"name": "Sale Batch Usages",  "description": "Trazabilidad de stock por lote en ventas."},
    {"name": "Refund Products",    "description": "Devoluciones de productos."},
    {"name": "Suppliers",          "description": "Proveedores de productos."},
    {"name": "Purchases",          "description": "Ordenes de compra a proveedores."},
    {"name": "Health Check",       "description": "Estado del servidor."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running database seeds...")
    from .seeds.init_db import init_db
    init_db()
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="PharmaTrack API",
    description="API REST para gestion de inventario y ventas de farmacia.",
    version="1.0.0",
    contact={"name": "PharmaTrack"},
    license_info={"name": "Proyecto academico"},
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    redirect_slashes=False,
    # Ocultar docs en produccion para no exponer el schema publico
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_CORS_ORIGINS = settings.allowed_origins if settings.is_production else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        loc = error.get("loc", [])
        # Drop the first segment ("body" / "query" / "path") — not useful for the frontend
        field_parts = [str(p) for p in loc[1:]] if len(loc) > 1 else [str(p) for p in loc]
        field = ".".join(field_parts) if field_parts else "unknown"
        errors.append({"field": field, "message": error["msg"]})
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url,
        exc,
        exc_info=True,
    )
    origin = request.headers.get("origin", "")
    cors_origin = origin if (origin and ("*" in _CORS_ORIGINS or origin in _CORS_ORIGINS)) else ""
    headers = {"Access-Control-Allow-Origin": cors_origin} if cors_origin else {}
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )


@app.get("/", tags=["Health Check"])
def root():
    return {"message": "PharmaTrack API", "version": "1.0.0", "status": "ok"}


@app.get("/healthcheck", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is running"}


app.include_router(api_v1_router)