"""
possystem/seeds/seed_product_categories.py

Seeds the full category tree.
Run this FIRST before any product seeder.
"""
from sqlalchemy.orm import Session
from possystem.db.session import SessionLocal
from possystem.seeds.helpers.seeder_helpers import get_or_create_category

# =========================================================
# 📂 Category tree
# =========================================================
PRODUCT_CATEGORIES = [
    {
        "name": "Medicamentos",
        "children": [
            {"name": "Analgésicos"},
            {"name": "Antiinflamatorios"},
            {"name": "Antigripales"},
            {"name": "Antibióticos"},
            {"name": "Antivirales"},
            {"name": "Antifúngicos"},
            {"name": "Antiparasitarios"},
            {"name": "Antihipertensivos"},
            {"name": "Anticoagulantes"},
            {"name": "Hipolipemiantes"},
            {"name": "Diabetes"},
            {"name": "Hormonas"},
            {"name": "Antialérgicos"},
            {"name": "Broncodilatadores"},
            {"name": "Antitusivos"},
            {"name": "Mucolíticos"},
            {"name": "Gastrointestinales"},
            {"name": "Oftalmológicos"},
            {"name": "Dermatológicos"},
            {"name": "Anticonceptivos"},
            {"name": "Pediátricos"},
        ],
    },
    {
        "name": "Material de curación",
        "children": [
            {"name": "Jeringas y agujas"},
            {"name": "Catéteres y sondas"},
            {"name": "Gasas y vendas"},
            {"name": "Cintas y parches"},
            {"name": "Algodón y torundas"},
            {"name": "Antisépticos y soluciones"},
            {"name": "Oxígeno y terapia respiratoria"},
            {"name": "Instrumental médico"},
            {"name": "Equipos y dispositivos médicos"},
            {"name": "Ortopedia y soporte"},
            {"name": "Desechables hospitalarios"},
            {"name": "Otros insumos médicos"},
        ],
    },
    {
        "name": "Cuidado personal y belleza",
        "children": [
            {"name": "Higiene personal"},
            {"name": "Cuidado de la piel"},
            {"name": "Cabello"},
            {"name": "Higiene dental"},
            {"name": "Salud sexual"},
            {"name": "Bebé y maternidad"},
            {"name": "Accesorios y herramientas"},
            {"name": "Dispositivos médicos"},
        ],
    },
    {
        "name": "Suplementos y nutrición",
        "children": [
            {"name": "Vitaminas"},
            {"name": "Minerales"},
            {"name": "Proteínas"},
            {"name": "Probióticos y prebióticos"},
            {"name": "Antioxidantes"},
            {"name": "Nutrición infantil"},
            {"name": "Nutrición especializada"},
            {"name": "Herbolaria"},
            {"name": "Omega y lípidos"},
            {"name": "Colágeno y belleza"},
            {"name": "Salud digestiva"},
            {"name": "Salud del sueño"},
        ],
    },
    {
        "name": "Alimentos y bebidas",
        "children": [
            {"name": "Chocolates"},
            {"name": "Caramelos y chicles"},
            {"name": "Bebidas"},
            {"name": "Paletas"},
            {"name": "Otros dulces"},
        ],
    },
    {
        "name": "Servicios farmacéuticos",
        "children": [
            {"name": "Consultas"},
            {"name": "Procedimientos"},
            {"name": "Diagnósticos rápidos"},
            {"name": "Documentos médicos"},
        ],
    },
    {
        "name": "Miscelánea y hogar",
        "children": [
            {"name": "Pilas y energía"},
            {"name": "Limpieza y desinfección"},
            {"name": "Papelería y oficina"},
            {"name": "Adhesivos y ferretería ligera"},
            {"name": "Higiene del hogar"},
            {"name": "Veterinaria"},
        ],
    },
    {
        "name": "Otros",
        "children": [],
    },
]


# =========================================================
# 🌱 Seeder
# =========================================================
def seed_product_categories(db: Session):
    total = 0

    for root_data in PRODUCT_CATEGORIES:
        get_or_create_category(db, root_data["name"])
        total += 1

        for child_data in root_data.get("children", []):
            get_or_create_category(db, child_data["name"], parent_name=root_data["name"])
            total += 1

    db.commit()
    print(f"✅ Categories seeded: {total} (roots + children)")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_product_categories(db)
    finally:
        db.close()