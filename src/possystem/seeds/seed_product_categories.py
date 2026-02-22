from sqlalchemy.orm import Session
from possystem.models.product_categories.orm import ProductCategory

# --- Categorías base de la farmacia ---
PRODUCT_CATEGORIES = [
    # ROOTS
    {
        "name": "Medicamentos",
        "children": [
            {"name": "Analgésicos"},
            {"name": "Antibióticos"},
            {"name": "Antiinflamatorios"},
            {"name": "Antigripales"},
            {"name": "Antihipertensivos"},
            {"name": "Diabetes"},
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
            {"name": "Proteínas"},
            {"name": "Minerales"},
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







def get_or_create_category(db: Session, name: str, parent: ProductCategory | None = None):
    category = (
        db.query(ProductCategory)
        .filter(ProductCategory.name == name, ProductCategory.parent_id == (parent.id if parent else None))
        .first()
    )

    if category:
        return category

    category = ProductCategory(
        name=name,
        parent_id=parent.id if parent else None,
        is_active=True,
        image=None
    )
    db.add(category)
    db.flush()  # 🔥 Important to get ID before children
    return category


def seed_product_categories(db: Session):
    created = 0

    for root_data in PRODUCT_CATEGORIES:
        root = get_or_create_category(db, root_data["name"])
        created += 1

        for child_data in root_data.get("children", []):
            child = get_or_create_category(db, child_data["name"], parent=root)
            created += 1

    db.commit()
    print(f"✅ Categories seeded (roots + children).")


if __name__ == "__main__":
    from possystem.db.session import SessionLocal

    db = SessionLocal()
    try:
        seed_product_categories(db)
    finally:
        db.close()



