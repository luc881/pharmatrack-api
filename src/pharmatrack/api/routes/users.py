from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from datetime import datetime, timezone
from ...db.session import get_db
from starlette import status
from passlib.context import CryptContext
from ...models.users.orm import User
from ...models.branches.orm import Branch
from ...models.roles.orm import Role
from ...models.users.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserDetailsResponse,
    UserSearchParams,
    ChangePasswordRequest,
    PaginatedResponse,
    PaginationParams,
)
from pharmatrack.models.products.schemas import BulkDeleteRequest
from ...utils.permissions import CAN_READ_USERS, CAN_CREATE_USERS, CAN_UPDATE_USERS, CAN_DELETE_USERS
from ...utils.security import user_dependency
from pharmatrack.utils.pagination import paginate
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE, LIMIT_SEARCH
from ...utils.logger import get_logger

logger = get_logger(__name__)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# =========================================================
# GET /me
# =========================================================
@router.get("/me",
            response_model=UserDetailsResponse,
            summary="Get current authenticated user",
            status_code=status.HTTP_200_OK)
async def get_me(db: db_dependency, token_data: user_dependency):
    user = db.query(User).filter(User.id == token_data["id"], User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# =========================================================
# GET /
# =========================================================
_USER_ORDERING_MAP = {
    "name":        User.name.asc(),
    "-name":       User.name.desc(),
    "created_at":  User.created_at.asc(),
    "-created_at": User.created_at.desc(),
}


@router.get("",
            response_model=PaginatedResponse[UserResponse],
            summary="List all users",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_USERS)
@limiter.limit(LIMIT_READ)
async def read_all(
    request: Request,
    db: db_dependency,
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    role_id: int | None = None,
    branch_id: int | None = None,
    gender: str | None = None,
    ordering: str | None = None,
):
    query = db.query(User).filter(User.deleted_at.is_(None))

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(User.name.ilike(term), User.surname.ilike(term), User.email.ilike(term))
        )
    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    if branch_id is not None:
        query = query.filter(User.branch_id == branch_id)
    if gender is not None:
        query = query.filter(User.gender == gender.upper())

    order_clause = _USER_ORDERING_MAP.get(ordering) if ordering else None
    query = query.order_by(order_clause if order_clause is not None else User.id.asc())

    return paginate(query, pagination)


# =========================================================
# GET /search
# =========================================================
@router.get("/search",
            response_model=PaginatedResponse[UserResponse],
            summary="Search users",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_USERS)
@limiter.limit(LIMIT_SEARCH)
async def search_users(
    request: Request,
    db: db_dependency,
    filters: UserSearchParams = Depends(),
    pagination: PaginationParams = Depends()
):
    if not any(getattr(filters, f) for f in type(filters).model_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar al menos un filtro para la búsqueda"
        )

    query = db.query(User).filter(User.deleted_at.is_(None))

    if filters.name:
        query = query.filter(User.name.ilike(f"%{filters.name}%"))
    if filters.surname:
        query = query.filter(User.surname.ilike(f"%{filters.surname}%"))
    if filters.email:
        query = query.filter(User.email.ilike(f"%{filters.email}%"))
    if filters.branch_id:
        query = query.filter(User.branch_id == filters.branch_id)
    if filters.role_id:
        query = query.filter(User.role_id == filters.role_id)
    if filters.phone:
        query = query.filter(User.phone.ilike(f"%{filters.phone}%"))
    if filters.gender:
        query = query.filter(User.gender == filters.gender)
    if filters.type_document:
        query = query.filter(cast(User.type_document, String).ilike(f"%{filters.type_document}%"))
    if filters.n_document:
        query = query.filter(User.n_document.ilike(f"%{filters.n_document}%"))

    return paginate(query, pagination)


# =========================================================
# GET /{user_id}
# =========================================================
@router.get("/{user_id}",
            response_model=UserResponse,
            summary="Get user by ID",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_USERS)
async def read_user_by_id(user_id: int, db: db_dependency):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# =========================================================
# GET /{user_id}/details
# =========================================================
@router.get("/{user_id}/details",
            response_model=UserDetailsResponse,
            summary="Get detailed user info",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_USERS)
async def read_user_details(user_id: int, db: db_dependency):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# =========================================================
# POST /
# =========================================================
@router.post("",
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_USERS)
@limiter.limit(LIMIT_WRITE)
async def create_user(request: Request, user: UserCreate, db: db_dependency):
    plain_password = user.password.get_secret_value()
    hashed = bcrypt_context.hash(plain_password)

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        logger.warning("Duplicate user creation attempt email=%s", user.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    if user.branch_id:
        if not db.query(Branch).filter(Branch.id == user.branch_id).first():
            raise HTTPException(status_code=404, detail="Branch not found")

    if user.role_id:
        if not db.query(Role).filter(Role.id == user.role_id).first():
            raise HTTPException(status_code=404, detail="Role not found")

    user_data = user.model_dump(mode="json")
    user_data["password"] = hashed

    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("User created id=%s email=%s", new_user.id, new_user.email)
    return new_user


# =========================================================
# PUT /{user_id}
# =========================================================
@router.put("/{user_id}",
            response_model=UserResponse,
            summary="Update a user",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_USERS)
async def update_user(user_id: int, user: UserUpdate, db: db_dependency):
    existing_user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.branch_id is not None:
        if not db.query(Branch).filter(Branch.id == user.branch_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    if user.role_id is not None:
        if not db.query(Role).filter(Role.id == user.role_id).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    user_data = user.model_dump(exclude_unset=True)

    if "avatar" in user_data:
        user_data["avatar"] = str(user_data["avatar"]) if user_data["avatar"] else None

    for key, value in user_data.items():
        setattr(existing_user, key, value)

    db.commit()
    db.refresh(existing_user)
    logger.info("User updated id=%s", user_id)
    return existing_user


# =========================================================
# PUT /{user_id}/change-password
# La validacion de fortaleza de contrasena la hace el schema
# ChangePasswordRequest via @field_validator (retorna 422).
# Aqui solo verificamos la contrasena vieja y el duplicado.
# =========================================================
@router.put("/{user_id}/change-password",
            summary="Change user password",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_USERS)
@limiter.limit(LIMIT_WRITE)
async def change_password(request: Request, user_id: int, data: ChangePasswordRequest, db: db_dependency, token_data: user_dependency):
    if token_data["id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change another user's password")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_pass = data.old_password.get_secret_value()
    if not bcrypt_context.verify(old_pass, user.password):
        logger.warning("Wrong old password attempt for user id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña anterior es incorrecta"
        )

    new_pass = data.new_password.get_secret_value()

    if bcrypt_context.verify(new_pass, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña no puede ser igual a la anterior."
        )

    user.password = bcrypt_context.hash(new_pass)
    db.commit()
    db.refresh(user)

    logger.info("Password changed for user id=%s", user_id)
    return {"message": "Contraseña actualizada correctamente"}


# =========================================================
# DELETE /bulk
# =========================================================
@router.delete("/bulk",
               status_code=status.HTTP_200_OK,
               summary="Bulk delete users",
               description="Deletes multiple users atomically. Fails if any ID does not exist.",
               dependencies=CAN_DELETE_USERS)
@limiter.limit(LIMIT_WRITE)
async def bulk_delete_users(request: Request, payload: BulkDeleteRequest, db: db_dependency):
    users = db.query(User).filter(User.id.in_(payload.ids), User.deleted_at.is_(None)).all()
    found_ids = {u.id for u in users}
    missing = [i for i in payload.ids if i not in found_ids]
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Users not found: {missing}")
    now = datetime.now(timezone.utc)
    for user in users:
        user.deleted_at = now
    db.commit()
    return {"deleted": len(users)}


# =========================================================
# DELETE /{user_id}
# =========================================================
@router.delete("/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Soft-delete a user",
               dependencies=CAN_DELETE_USERS)
@limiter.limit(LIMIT_WRITE)
async def delete_user(request: Request, user_id: int, db: db_dependency):
    existing_user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing_user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("User soft-deleted id=%s", user_id)
    return None


# =========================================================
# PATCH /{user_id}/restore
# =========================================================
@router.patch("/{user_id}/restore",
              status_code=status.HTTP_200_OK,
              response_model=UserResponse,
              summary="Restore a soft-deleted user",
              dependencies=CAN_UPDATE_USERS)
async def restore_user(user_id: int, db: db_dependency):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.isnot(None)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or not deleted")
    user.deleted_at = None
    db.commit()
    db.refresh(user)
    logger.info("User restored id=%s", user_id)
    return user