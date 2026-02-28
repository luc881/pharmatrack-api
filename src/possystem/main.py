from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .logging_config import setup_logging

# ✅ Debe llamarse ANTES de importar los routers
# para que todos sus loggers ya estén configurados al crearse
setup_logging()

from .api.routes import (
    permissions, roles, users, branches, auth,
    product_categories, products, sales, sale_payments,
    sale_details, refund_products, suppliers, purchases,
    purchase_details, product_batch, sale_batch_usage,
    product_master, product_brand, ingredients
)

# =========================================================
# 🔹 Logger de este módulo
# =========================================================
logger = logging.getLogger(__name__)


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
app = FastAPI(lifespan=lifespan)


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
# 🔹 Endpoints base
# =========================================================
@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the POS System API"}


@app.get("/healthcheck", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is running"}


# =========================================================
# 🔹 Routers
# =========================================================
app.include_router(auth.router)
app.include_router(permissions.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(branches.router)
app.include_router(ingredients.router)
app.include_router(product_brand.router)
app.include_router(products.router)
app.include_router(product_batch.router)
app.include_router(product_master.router)
app.include_router(product_categories.router)
app.include_router(sales.router)
app.include_router(sale_payments.router)
app.include_router(sale_details.router)
app.include_router(refund_products.router)
app.include_router(suppliers.router)
app.include_router(purchases.router)
# app.include_router(purchase_details.router)