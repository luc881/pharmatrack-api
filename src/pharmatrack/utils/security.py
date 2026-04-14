from fastapi import Depends, HTTPException
from starlette import status
from ..models.users.orm import User
from typing import Annotated
from sqlalchemy.orm import Session
from ..db.session import get_db
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
import secrets
from pharmatrack.config import settings

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db_dependency = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
oauth2_dependency = Annotated[str, Depends(oauth2_scheme)]
auth_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]

# =========================================================
# 🔹 Constantes
# =========================================================
REFRESH_TOKEN_EXPIRE_DAYS = 7


# =========================================================
# 🔹 Autenticación
# =========================================================
def authenticate_user(db, email: str, password: str):
    user_model = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if not user_model or not bcrypt_context.verify(password, user_model.password):
        return False
    return user_model


# =========================================================
# 🔹 Access Token (JWT)
# =========================================================
def create_jwt_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {
        "sub": username,
        "id": user_id,
        "role": role
    }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, settings.secret_key, algorithm=settings.algorithm)


async def decode_jwt_token(token: oauth2_dependency):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise credentials_exception
        return {"username": username, "id": user_id, "user_role": user_role}
    except JWTError:
        raise credentials_exception


user_dependency = Annotated[dict, Depends(decode_jwt_token)]


# =========================================================
# 🔹 Refresh Token
# =========================================================
def create_refresh_token() -> str:
    """
    Genera un token aleatorio seguro para usar como refresh token.
    No es JWT — es un string opaco guardado en la BD.
    """
    return secrets.token_urlsafe(64)


def save_refresh_token(db: Session, user_id: int, refresh_token: str) -> None:
    """Guarda el refresh token y su fecha de expiración en el usuario."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.remember_token = refresh_token
        user.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        db.commit()


def validate_refresh_token(db: Session, refresh_token: str) -> User:
    """
    Busca el usuario que tiene ese refresh token.
    Lanza 401 si no existe, ya fue invalidado, o expiró.
    """
    user = db.query(User).filter(User.remember_token == refresh_token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    if user.refresh_token_expires_at and user.refresh_token_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        user.remember_token = None
        user.refresh_token_expires_at = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    return user


def revoke_refresh_token(db: Session, user_id: int) -> None:
    """Invalida el refresh token del usuario (logout)."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.remember_token = None
        db.commit()


# =========================================================
# 🔹 Permisos
# =========================================================
def require_permission(permission: str):
    async def checker(
        token_data: user_dependency,
        db: db_dependency
    ):
        user = db.query(User).filter(User.id == token_data["id"], User.deleted_at.is_(None)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        if not user.role or user.role.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role not assigned"
            )

        user_permissions = {perm.name for perm in user.role.permissions}

        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        return token_data
    return checker