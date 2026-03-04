from fastapi import Depends, HTTPException, APIRouter, Request
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
from ...utils.rate_limit import limiter, LIMIT_AUTH, LIMIT_WRITE
from ...utils.logger import get_logger

logger = get_logger(__name__)

db_dependency = Annotated[Session, Depends(get_db)]
auth_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


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

    access_token = create_jwt_token(
        username=user.email,
        user_id=user.id,
        role=user.role.name if user.role else None,
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

    new_access_token = create_jwt_token(
        username=user.email,
        user_id=user.id,
        role=user.role.name if user.role else None,
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