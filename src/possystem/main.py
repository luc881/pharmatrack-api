from fastapi import FastAPI
from contextlib import asynccontextmanager
from .api.routes import (
    permissions, roles, users, branches, auth,
    product_categories, products, sales, sale_payments,
    sale_details, refund_products, suppliers, purchases,
    purchase_details, product_batch, sale_batch_usage,
    product_master, product_brand, ingredients
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — las tablas ya las maneja Alembic, solo corremos seeds
    print("🌱 Running database seeds...")
    from .seeds.init_db import init_db
    init_db()

    yield

    print("🛑 Application shutdown")


app = FastAPI(lifespan=lifespan)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the POS System API"}


@app.get("/healthcheck", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is running"}


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