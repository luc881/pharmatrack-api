from sqlalchemy.orm import Session
from pharmatrack.models.users.orm import User
from pharmatrack.models.roles.orm import Role
from pharmatrack.db.session import SessionLocal
from passlib.context import CryptContext

# Configuración para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def seed_superuser(db: Session):
    """
    Crea un usuario administrador principal (superuser) si no existe.
    """

    SUPERUSER_EMAIL = "admin@pharmatrack.com"
    SUPERUSER_PASSWORD = "1278972"
    SUPERUSER_NAME = "Adm"
    SUPERUSER_SURNAME = "Principal"

    # Buscar rol admin
    admin_role = db.query(Role).filter_by(name="admin").first()
    if not admin_role:
        raise ValueError("❌ No se encontró el rol 'admin'. Ejecuta primero seed_roles.py")

    # Verificar si ya existe un superuser
    existing_user = db.query(User).filter_by(email=SUPERUSER_EMAIL).first()

    if existing_user:
        print(f"ℹ️ El usuario superadmin ya existe: {SUPERUSER_EMAIL}")
        return

    # Crear usuario
    superuser = User(
        name=SUPERUSER_NAME,
        surname=SUPERUSER_SURNAME,
        email=SUPERUSER_EMAIL,
        password=get_password_hash(SUPERUSER_PASSWORD),
        role_id=admin_role.id,
        email_verified_at=None,
        gender=None,
        avatar=None,
        phone=None,
        type_document=None,
        n_document=None,
        branch_id=None,
    )

    db.add(superuser)
    db.commit()

    print(f"✅ Superusuario creado correctamente: {SUPERUSER_EMAIL}")
    print(f"   Contraseña: {SUPERUSER_PASSWORD}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_superuser(db)
    finally:
        db.close()
