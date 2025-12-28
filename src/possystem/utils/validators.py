from fastapi import HTTPException
from starlette import status
from possystem.models.products.schemas import ProductBase
from possystem.models.products.orm import Product
from possystem.models.products.schemas import ProductUpdate

INVALID_UNIT_NAMES_FOR_UNIT_SALE = {
    "caja",
    "paquete",
    "pack",
    "blister",
    "frasco"
}


def validate_units_schema(data: ProductBase):
    if data.is_unit_sale:
        if data.base_unit_name or data.units_per_base:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit sale product cannot define base units"
            )
    else:
        if not data.base_unit_name or not data.units_per_base:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pack product must define base unit and quantity"
            )


def merge_product_units(product: Product, update: ProductUpdate) -> ProductBase:
    return ProductBase(
        is_unit_sale=update.is_unit_sale if update.is_unit_sale is not None else product.is_unit_sale,
        unit_name=update.unit_name if update.unit_name is not None else product.unit_name,
        base_unit_name=update.base_unit_name if update.base_unit_name is not None else product.base_unit_name,
        units_per_base=update.units_per_base if update.units_per_base is not None else product.units_per_base,
        price_retail=product.price_retail,
        price_cost=product.price_cost,
        title=product.title,
    )

def validate_unit_name_for_sale(data: ProductBase):
    if data.is_unit_sale:
        if data.unit_name.lower() in INVALID_UNIT_NAMES_FOR_UNIT_SALE:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid unit_name '{data.unit_name}' for unit sale"
            )


def normalize_units(data: ProductBase):
    """
    Normaliza los campos de unidades según is_unit_sale.

    Reglas:
    - Si is_unit_sale=True:
        - base_unit_name y units_per_base se ponen en None
        - unit_name no puede ser un valor inválido (caja, paquete, etc.)
    - Si is_unit_sale=False:
        - base_unit_name y units_per_base deben existir (se valida aparte)
    """
    if data.is_unit_sale:
        # Limpiar fraccionamiento
        data.base_unit_name = None
        data.units_per_base = None

        # Opcional: normalizar unit_name a minúsculas
        if data.unit_name:
            data.unit_name = data.unit_name.strip().lower()
    else:
        # Para productos en pack, normalizar nombres
        if data.unit_name:
            data.unit_name = data.unit_name.strip().lower()
        if data.base_unit_name:
            data.base_unit_name = data.base_unit_name.strip().lower()
