from sqlalchemy.orm import Session
from pharmatrack.models.roles.orm import Role
from pharmatrack.models.permissions.orm import Permission
from pharmatrack.db.session import SessionLocal


def seed_roles(db: Session):
    """
    Crea roles base para el sistema y les asigna los permisos correspondientes.
    """

    # --- Permisos agrupados por rol ---
    role_permissions = {
        "admin": [  # Acceso total
            "*"
        ],

        # "inventory_manager": [  # Encargado de inventario / almacén
        #     "products.*",
        #     "productscategories.*",
        #     "warehouses.*",
        #     "productwarehouses.*",
        #     "productstockinitials.*",
        #     "suppliers.*",
        #     "purchases.*",
        #     "purchasedetails.*",
        #     "conversions.*",
        # ],
        #
        # "seller": [  # Vendedor / cajero
        #     "sales.*",
        #     "salepayments.*",
        #     "saledetails.*",
        #     "saledetailattentions.*",
        #     "clients.*",
        #     "refundproducts.*",
        #     "products.read",
        # ],
        #
        # "viewer": [  # Rol de solo lectura
        #     "*.read",
        # ],
    }

    created_count = 0
    updated_count = 0

    # --- Recuperamos todos los permisos existentes ---
    all_permissions = db.query(Permission).all()
    perm_map = {p.name: p for p in all_permissions}

    # --- Helper para hacer matching tipo wildcard ("*") ---
    def match_permissions(patterns: list[str]):
        matched = set()
        for pattern in patterns:
            if pattern == "*":
                matched.update(all_permissions)
            elif pattern.endswith(".*"):
                prefix = pattern[:-2]
                matched.update([p for name, p in perm_map.items() if name.startswith(prefix)])
            else:
                if pattern in perm_map:
                    matched.add(perm_map[pattern])
        return list(matched)

    # --- Crear o actualizar roles ---
    for role_name, perm_patterns in role_permissions.items():
        role = db.query(Role).filter_by(name=role_name).first()
        perms = match_permissions(perm_patterns)

        if not role:
            role = Role(name=role_name)
            role.permissions = perms
            db.add(role)
            created_count += 1
        else:
            role.permissions = perms
            updated_count += 1

    db.commit()

    print(f"✅ Seeding completado: {created_count} roles creados, {updated_count} actualizados.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()
