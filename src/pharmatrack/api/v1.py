from fastapi import APIRouter
from .routes import (
    permissions, roles, users, branches, auth,
    product_categories, products, sales, sale_payments,
    sale_details, refund_products, suppliers, purchases,
    purchase_details, product_batch, sale_batch_usage,
    product_master, product_brand, ingredients, stats, sensor_readings
)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(permissions.router)
api_v1_router.include_router(roles.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(branches.router)
api_v1_router.include_router(ingredients.router)
api_v1_router.include_router(product_brand.router)
api_v1_router.include_router(products.router)
api_v1_router.include_router(product_batch.router)
api_v1_router.include_router(product_master.router)
api_v1_router.include_router(product_categories.router)
api_v1_router.include_router(sales.router)
api_v1_router.include_router(sale_payments.router)
api_v1_router.include_router(sale_details.router)
api_v1_router.include_router(sale_batch_usage.router)   # ← montado
api_v1_router.include_router(refund_products.router)
api_v1_router.include_router(suppliers.router)
api_v1_router.include_router(purchases.router)
api_v1_router.include_router(purchase_details.router)
api_v1_router.include_router(stats.router)
api_v1_router.include_router(sensor_readings.router)