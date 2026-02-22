from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.models.products.orm import Product
from possystem.seeds.helpers.services import get_or_create_category, create_service


SERVICIOS_MEDICOS = [
    {"sku": "01", "title": "Consulta", "price": 60, "cat": "Consultas"},
    {"sku": "02", "title": "Aplicación", "price": 20, "cat": "Procedimientos"},
    {"sku": "03", "title": "Certificado médico", "price": 70, "cat": "Documentos médicos"},
    {"sku": "04", "title": "Toma de presión", "price": 15, "cat": "Diagnósticos rápidos"},
    {"sku": "07", "title": "Justificante médico", "price": 100, "cat": "Documentos médicos"},

    # Domingo premium
    {"sku": "D01", "title": "Consulta domingo", "price": 75, "cat": "Consultas"},
    {"sku": "D02", "title": "Aplicación domingo", "price": 25, "cat": "Procedimientos"},
    {"sku": "D03", "title": "Certificado domingo", "price": 70, "cat": "Documentos médicos"},
    {"sku": "D04", "title": "Presión domingo", "price": 20, "cat": "Diagnósticos rápidos"},
    {"sku": "D05", "title": "Glucosa domingo", "price": 50, "cat": "Diagnósticos rápidos"},
    {"sku": "D06", "title": "Sutura domingo", "price": 150, "cat": "Procedimientos"},
    {"sku": "D07", "title": "Justificante domingo", "price": 120, "cat": "Documentos médicos"},
]


def seed_servicios_medicos(db: Session):

    # ROOT
    root = "Servicios farmacéuticos"
    get_or_create_category(db, root)

    # SUBCATS
    cats = {
        "Consultas": get_or_create_category(db, "Consultas", root),
        "Procedimientos": get_or_create_category(db, "Procedimientos", root),
        "Diagnósticos rápidos": get_or_create_category(db, "Diagnósticos rápidos", root),
        "Documentos médicos": get_or_create_category(db, "Documentos médicos", root),
    }

    created = 0
    skipped = 0

    for s in SERVICIOS_MEDICOS:
        service = create_service(
            db=db,
            sku=s["sku"],
            title=s["title"],
            price=float(s["price"]),
            category_id=cats[s["cat"]],
        )

        if service:
            created += 1
        else:
            skipped += 1

    db.commit()
    print(f"✅ Servicios creados: {created}")
    print(f"⚠️ Duplicados omitidos: {skipped}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_servicios_medicos(db)
    finally:
        db.close()