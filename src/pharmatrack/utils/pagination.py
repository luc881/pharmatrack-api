from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Query as SQLAQuery

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Número de página")
    page_size: int = Field(default=20, ge=1, le=500, description="Items por página")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 20
            }
        }
    )


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "data": [],
                "total": 87,
                "page": 2,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_prev": True
            }
        }
    )


def paginate(query: SQLAQuery, params: PaginationParams) -> dict:
    """
    Recibe una query de SQLAlchemy ya filtrada y los parámetros de paginación.
    Retorna un dict compatible con PaginatedResponse.
    """
    total = query.count()
    items = query.offset(params.offset).limit(params.page_size).all()
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 1

    return {
        "data": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
        "has_next": params.page < total_pages,
        "has_prev": params.page > 1,
    }
