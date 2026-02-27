"""
possystem/seeds/seed_products_serviciosmedicos.py

Services are products with price_cost=0 and price_retail=sale price.
"""
from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.seeds.helpers.seeder_helpers import (
    get_or_create_category,
    get_or_create_product,
)

ROOT = "Servicios farmacéuticos"

SERVICIOS_MEDICOS = [
    {"sku": "01",  "title": "Consulta",             "price": 60,  "cat": "Consultas"},
    {"sku": "02",  "title": "Aplicación",            "price": 20,  "cat": "Procedimientos"},
    {"sku": "03",  "title": "Certificado médico",    "price": 70,  "cat": "Documentos médicos"},
    {"sku": "04",  "title": "Toma de presión",       "price": 15,  "cat": "Diagnósticos rápidos"},
    {"sku": "07",  "title": "Justificante médico",   "price": 100, "cat": "Documentos médicos"},
    {"sku": "D01", "title": "Consulta domingo",      "price": 75,  "cat": "Consultas"},
    {"sku": "D02", "title": "Aplicación domingo",    "price": 25,  "cat": "Procedimientos"},
    {"sku": "D03", "title": "Certificado domingo",   "price": 70,  "cat": "Documentos médicos"},
    {"sku": "D04", "title": "Presión domingo",       "price": 20,  "cat": "Diagnósticos rápidos"},
    {"sku": "D05", "title": "Glucosa domingo",       "price": 50,  "cat": "Diagnósticos rápidos"},
    {"sku": "D06", "title": "Sutura domingo",        "price": 150, "cat": "Procedimientos"},
    {"sku": "D07", "title": "Justificante domingo",  "price": 120, "cat": "Documentos médicos"},
]


def seed_servicios_medicos(db: Session):
    created = skipped = 0

    for s in SERVICIOS_MEDICOS:
        category_id = get_or_create_category(db, s["cat"], ROOT)

        _, was_created = get_or_create_product(
            db,
            title=s["title"],
            sku=s["sku"],
            brand_id=None,
            category_id=category_id,
            price_cost=0.0,
            price_retail=float(s["price"]),
            description=f"Servicio: {s['title']}",
            unit_name="servicio",
            is_unit_sale=False,
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Servicios creados:    {created}")
    print(f"⚠️  Duplicados omitidos: {skipped}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_servicios_medicos(db)
    finally:
        db.close()