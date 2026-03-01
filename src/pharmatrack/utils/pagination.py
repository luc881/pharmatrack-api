from sqlalchemy.orm import Query as SQLAQuery
from pharmatrack.models.products.schemas import PaginationParams


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