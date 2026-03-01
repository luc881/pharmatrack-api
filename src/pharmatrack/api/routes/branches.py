from fastapi import Depends, HTTPException, APIRouter
from starlette import status
from ...models.branches.orm import Branch
from typing import Annotated
from sqlalchemy.orm import Session
from ...models.branches.schemas import BranchResponse, BranchBase, BranchUpdate,BranchWithUsersResponse
from ...db.session import get_db
from ...utils.permissions import CAN_READ_BRANCHES, CAN_CREATE_BRANCHES, CAN_UPDATE_BRANCHES, CAN_DELETE_BRANCHES

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/branches",
    tags=["Branches"]
)


@router.get('/',
            response_model=list[BranchResponse],
            summary="List all branches",
            description="Retrieve all branches currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_BRANCHES
            )
async def read_all(db: db_dependency):
    branches = db.query(Branch).all()
    return branches


@router.get('/{branch_id}',
            response_model=BranchResponse,
            summary="Get a branch by ID",
            description="Retrieve a specific branch by its ID.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_BRANCHES)
async def read_by_id(branch_id: int, db: db_dependency):
    branch_model = db.query(Branch).filter(Branch.id == branch_id).first()

    if not branch_model:
        raise HTTPException(status_code=404, detail='Branch not found')

    return branch_model


@router.get('/{branch_id}/users',
            summary="Get users by branch ID",
            description="Retrieve all users associated with a specific branch by its ID.",
            response_model = BranchWithUsersResponse,
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_BRANCHES)
async def read_users_by_branch(branch_id: int, db: db_dependency):
    branch_model = db.query(Branch).filter(Branch.id == branch_id).first()

    if not branch_model:
        raise HTTPException(status_code=404, detail='Branch not found')

    return branch_model


@router.post('/',
            status_code=status.HTTP_201_CREATED,
            response_model=BranchResponse,
            summary="Create a new branch",
            description="Adds a new branch to the database. The branch name must be unique.",
            dependencies=CAN_CREATE_BRANCHES)
async def create_branch(db: db_dependency, branch_request: BranchBase):
    branch_model = Branch(**branch_request.model_dump())

    branch_found = db.query(Branch).filter(Branch.name.ilike(branch_model.name)).first()

    if branch_found:
        raise HTTPException(status_code=409, detail='Branch already exists')

    db.add(branch_model)
    db.commit()
    db.refresh(branch_model)
    return branch_model


@router.put('/{branch_id}',
            status_code=status.HTTP_200_OK,
            response_model=BranchResponse,
            summary="Update a branch",
            description="Updates an existing branch in the database.",
            dependencies=CAN_UPDATE_BRANCHES)
async def update_branch(branch_id: int, db: db_dependency, branch_request: BranchUpdate):
    branch_model = db.query(Branch).filter(Branch.id == branch_id).first()

    if not branch_model:
        raise HTTPException(status_code=404, detail='Branch not found')

    for key, value in branch_request.model_dump(exclude_unset=True).items():
        setattr(branch_model, key, value)

    db.commit()
    db.refresh(branch_model)
    return branch_model


@router.delete('/{branch_id}',
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete a branch",
            description="Deletes an existing branch from the database.",
            dependencies=CAN_DELETE_BRANCHES)
async def delete_branch(branch_id: int, db: db_dependency):
    branch_model = db.query(Branch).filter(Branch.id == branch_id).first()

    if not branch_model:
        raise HTTPException(status_code=404, detail='Branch not found')

    db.delete(branch_model)
    db.commit()
    return None
