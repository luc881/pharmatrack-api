from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ...db.session import get_db
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from starlette import status
from ...utils.security import (
    authenticate_user,
    create_jwt_token,
    create_refresh_token,
    save_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    user_dependency,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

db_dependency = Annotated[Session, Depends(get_db)]
auth_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]


# =========================================================
# 🔹 Schema para recibir el refresh token
# =========================================================
class RefreshTokenRequest(BaseModel):
    refresh_token: str


# =========================================================
# 🔹 Router
# =========================================================
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# =========================================================
# 🔹 Login
# =========================================================
@router.post("/token")
async def login_user(form_data: auth_dependency, db: db_dependency):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Access token — corta duración
    access_token = create_jwt_token(
        username=user.email,
        user_id=user.id,
        role=user.role.name if user.role else None,
        expires_delta=timedelta(minutes=30)
    )

    # Refresh token — larga duración, guardado en BD
    refresh_token = create_refresh_token()
    save_refresh_token(db, user.id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,  # segundos
        "message": "Successful login"
    }


# =========================================================
# 🔹 Refresh — obtener nuevo access token
# =========================================================
@router.post("/refresh")
async def refresh_access_token(payload: RefreshTokenRequest, db: db_dependency):
    # Valida que el refresh token exista en la BD
    user = validate_refresh_token(db, payload.refresh_token)

    # Genera nuevo access token
    new_access_token = create_jwt_token(
        username=user.email,
        user_id=user.id,
        role=user.role.name if user.role else None,
        expires_delta=timedelta(minutes=30)
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
    }


# =========================================================
# 🔹 Logout — invalidar refresh token
# =========================================================
@router.post("/logout")
async def logout(token_data: user_dependency, db: db_dependency):
    revoke_refresh_token(db, token_data["id"])
    return {"message": "Successfully logged out"}