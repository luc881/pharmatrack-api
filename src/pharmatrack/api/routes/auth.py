from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from ...db.session import get_db
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
from starlette import status
import secrets
from ...utils.security import (
    authenticate_user,
    create_jwt_token,
    create_refresh_token,
    save_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    user_dependency,
    REFRESH_TOKEN_EXPIRE_DAYS,
    bcrypt_context,
)
from ...utils.rate_limit import limiter, LIMIT_AUTH, LIMIT_WRITE
from ...utils.logger import get_logger
from ...models.users.orm import User
from ...models.password_reset_tokens.orm import PasswordResetToken

logger = get_logger(__name__)

db_dependency = Annotated[Session, Depends(get_db)]
auth_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]

PASSWORD_RESET_EXPIRE_MINUTES = 15


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# =========================================================
# POST /token
# =========================================================
@router.post("/token")
@limiter.limit(LIMIT_AUTH)
async def login_user(request: Request, form_data: auth_dependency, db: db_dependency):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning("Failed login attempt for email=%s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    permissions = [p.name for p in user.role.permissions] if user.role else []
    access_token = create_jwt_token(
        username=user.email,
        user_id=user.id,
        role=user.role.name if user.role else None,
        permissions=permissions,
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = create_refresh_token()
    save_refresh_token(db, user.id, refresh_token)

    logger.info("User logged in id=%s email=%s", user.id, user.email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
        "message": "Successful login"
    }


# =========================================================
# POST /refresh
# =========================================================
@router.post("/refresh")
@limiter.limit(LIMIT_WRITE)
async def refresh_access_token(request: Request, payload: RefreshTokenRequest, db: db_dependency):
    user = validate_refresh_token(db, payload.refresh_token)

    permissions = [p.name for p in user.role.permissions] if user.role else []
    new_access_token = create_jwt_token(
        username=user.email,
        user_id=user.id,
        role=user.role.name if user.role else None,
        permissions=permissions,
        expires_delta=timedelta(minutes=30)
    )

    logger.info("Token refreshed for user id=%s", user.id)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
    }


# =========================================================
# POST /logout
# =========================================================
@router.post("/logout")
@limiter.limit(LIMIT_WRITE)
async def logout(request: Request, token_data: user_dependency, db: db_dependency):
    revoke_refresh_token(db, token_data["id"])
    logger.info("User logged out id=%s", token_data["id"])
    return {"message": "Successfully logged out"}


# =========================================================
# POST /forgot-password
# =========================================================
_FORGOT_RESPONSE = {"message": "Si el correo existe recibirás un link para restablecer tu contraseña"}

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Solicitar reset de contraseña",
)
@limiter.limit(LIMIT_AUTH)
async def forgot_password(request: Request, payload: ForgotPasswordRequest, db: db_dependency):
    from ...utils.email import send_password_reset_email

    user = db.query(User).filter(
        User.email == payload.email,
        User.deleted_at.is_(None),
    ).first()

    # Siempre devolver la misma respuesta — no revelar si el email existe
    if not user:
        return _FORGOT_RESPONSE

    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at,
        used=False,
    )
    db.add(reset_token)
    db.commit()

    try:
        send_password_reset_email(to_email=user.email, token=token)
    except Exception as e:
        logger.error("Password reset email FAILED for user id=%s error=%s", user.id, e, exc_info=True)

    logger.info("Password reset requested for user id=%s", user.id)
    return _FORGOT_RESPONSE


# =========================================================
# POST /reset-password
# =========================================================
@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña con token",
)
@limiter.limit(LIMIT_AUTH)
async def reset_password(request: Request, payload: ResetPasswordRequest, db: db_dependency):
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == payload.token,
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token ya fue utilizado",
        )

    if reset_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    user.password = bcrypt_context.hash(payload.new_password)
    reset_token.used = True
    db.commit()

    logger.info("Password reset completed for user id=%s", user.id)
    return {"message": "Contraseña actualizada correctamente"}