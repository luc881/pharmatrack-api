from fastapi import Depends, HTTPException, APIRouter
from starlette import status
from datetime import datetime, timezone
from ...models.roles.orm import Role
from typing import Annotated
from sqlalchemy.orm import Session
from ...models.roles.schemas import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    RoleWithPermissions,
    PaginatedResponse,
    PaginationParams,
)
from pharmatrack.models.products.schemas import BulkDeleteRequest
from ...models.permissions.orm import Permission
from ...db.session import get_db
from ...utils.permissions import CAN_READ_ROLES, CAN_CREATE_ROLES, CAN_UPDATE_ROLES, CAN_DELETE_ROLES

from pharmatrack.utils.pagination import paginate

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


@router.get("",
            response_model=PaginatedResponse[RoleResponse],
            summary="List all roles",
            description="Retrieve all roles currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_ROLES)
async def read_all(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(Role).filter(Role.deleted_at.is_(None)).order_by(Role.id.asc())
    return paginate(query, pagination)


@router.get("/permissions",
            response_model=PaginatedResponse[RoleWithPermissions],
            summary="List all roles with permissions",
            description="Retrieve all roles along with their associated permissions.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_ROLES)
async def read_all_with_permissions(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(Role).filter(Role.deleted_at.is_(None)).order_by(Role.id.asc())
    return paginate(query, pagination)


@router.get("/{role_id}",
            response_model=RoleWithPermissions,
            summary="Get a role by ID",
            description="Retrieve a specific role by its ID, including associated permissions.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_ROLES)
async def read_by_id_with_permissions(role_id: int, db: db_dependency):
    role = db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post("",
            status_code=status.HTTP_201_CREATED,
            response_model=RoleWithPermissions,
            summary="Create a new role with optional permissions",
            description="Adds a new role to the database. The role name must be unique. You can include permission IDs to associate them automatically.",
            dependencies=CAN_CREATE_ROLES)
async def create_role(db: db_dependency, role_request: RoleCreate):
    role_found = db.query(Role).filter(Role.name.ilike(role_request.name)).first()
    if role_found:
        raise HTTPException(status_code=409, detail="Role name already exists")

    role_model = Role(name=role_request.name)
    db.add(role_model)
    db.commit()
    db.refresh(role_model)

    if role_request.permission_ids:
        permissions = (
            db.query(Permission)
            .filter(Permission.id.in_(role_request.permission_ids))
            .all()
        )

        if not permissions:
            raise HTTPException(status_code=404, detail="No valid permissions found")

        found_ids = {p.id for p in permissions}
        missing_ids = set(role_request.permission_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Permissions not found: {list(missing_ids)}"
            )

        role_model.permissions.extend(permissions)
        db.commit()
        db.refresh(role_model)

    return role_model


@router.put("/{role_id}",
            status_code=status.HTTP_200_OK,
            response_model=RoleWithPermissions,
            summary="Update an existing role (and optionally its permissions)",
            description="Updates the details of an existing role by ID. You can update the name and optionally reassign permissions.",
            dependencies=CAN_UPDATE_ROLES)
async def update_role(role_id: int, db: db_dependency, role_request: RoleUpdate):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role_request.name:
        existing_role = (
            db.query(Role)
            .filter(Role.name.ilike(role_request.name))
            .first()
        )
        if existing_role and existing_role.id != role_id:
            raise HTTPException(status_code=409, detail="Role name already exists")
        role.name = role_request.name

    if role_request.permission_ids is not None:
        permissions = (
            db.query(Permission)
            .filter(Permission.id.in_(role_request.permission_ids))
            .all()
        )

        if not permissions and role_request.permission_ids:
            raise HTTPException(status_code=404, detail="No valid permissions found")

        found_ids = {p.id for p in permissions}
        missing_ids = set(role_request.permission_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Permissions not found: {list(missing_ids)}"
            )

        role.permissions = permissions

    db.commit()
    db.refresh(role)
    return role


@router.delete("/bulk",
            status_code=status.HTTP_200_OK,
            summary="Bulk soft-delete roles",
            description="Soft-deletes multiple roles atomically. Fails if any ID does not exist or is already deleted.",
            dependencies=CAN_DELETE_ROLES)
async def bulk_delete_roles(payload: BulkDeleteRequest, db: db_dependency):
    roles = db.query(Role).filter(Role.id.in_(payload.ids), Role.deleted_at.is_(None)).all()
    found_ids = {r.id for r in roles}
    missing = [i for i in payload.ids if i not in found_ids]
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Roles not found: {missing}")
    now = datetime.now(timezone.utc)
    for role in roles:
        role.deleted_at = now
    db.commit()
    return {"deleted": len(roles)}


@router.delete("/{role_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Soft-delete a role",
            description="Marks a role as deleted without removing it from the database.",
            dependencies=CAN_DELETE_ROLES)
async def delete_role(role_id: int, db: db_dependency):
    role = db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None)).one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.patch("/{role_id}/restore",
            status_code=status.HTTP_200_OK,
            response_model=RoleWithPermissions,
            summary="Restore a soft-deleted role",
            dependencies=CAN_UPDATE_ROLES)
async def restore_role(role_id: int, db: db_dependency):
    role = db.query(Role).filter(Role.id == role_id, Role.deleted_at.isnot(None)).one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found or not deleted")
    role.deleted_at = None
    db.commit()
    db.refresh(role)
    return role