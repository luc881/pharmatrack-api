"""Artículos de divulgación: CRUD admin + endpoints públicos.

El público lee /public/articles (solo publicados, sin auth). El detalle
se pide por id — el sitio arma el slug "titulo-id" client-side, igual
que con las especies del catálogo.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from starlette import status

from ...db.session import db_dependency
from ...models.articles.orm import Article
from ...models.articles.schemas import ArticleCreate, ArticleUpdate, ArticleResponse
from ...utils.permissions import (
    CAN_READ_ARTICLES,
    CAN_CREATE_ARTICLES,
    CAN_UPDATE_ARTICLES,
    CAN_DELETE_ARTICLES,
)

router = APIRouter(prefix="/articles", tags=["Articles"])
public_router = APIRouter(prefix="/public/articles", tags=["Public"])


def _apply_published(article: Article, published: bool):
    if published and article.published_at is None:
        article.published_at = datetime.utcnow()
    elif not published:
        article.published_at = None


# =========================================================
# Admin
# =========================================================
@router.get("", response_model=list[ArticleResponse], summary="List articles (incl. drafts)",
            dependencies=CAN_READ_ARTICLES)
async def list_articles(db: db_dependency):
    return db.query(Article).order_by(Article.updated_at.desc()).all()


@router.get("/{article_id}", response_model=ArticleResponse, summary="Get an article",
            dependencies=CAN_READ_ARTICLES)
async def get_article(article_id: int, db: db_dependency):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    return article


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED,
             summary="Create an article", dependencies=CAN_CREATE_ARTICLES)
async def create_article(payload: ArticleCreate, db: db_dependency):
    data = payload.model_dump(exclude={"published"})
    article = Article(**data)
    _apply_published(article, payload.published)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.put("/{article_id}", response_model=ArticleResponse, summary="Update an article",
            dependencies=CAN_UPDATE_ARTICLES)
async def update_article(article_id: int, payload: ArticleUpdate, db: db_dependency):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")

    data = payload.model_dump(exclude_unset=True, exclude={"published"})
    for key, value in data.items():
        setattr(article, key, value)

    if payload.published is not None:
        _apply_published(article, payload.published)

    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete an article", dependencies=CAN_DELETE_ARTICLES)
async def delete_article(article_id: int, db: db_dependency):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    db.delete(article)
    db.commit()


# =========================================================
# Público (sin auth): solo publicados
# =========================================================
@public_router.get("", response_model=list[ArticleResponse],
                   summary="Published articles for the public site")
async def public_list_articles(db: db_dependency):
    return (
        db.query(Article)
        .filter(Article.published_at.isnot(None))
        .order_by(Article.published_at.desc())
        .all()
    )


@public_router.get("/{article_id}", response_model=ArticleResponse,
                   summary="Published article detail")
async def public_get_article(article_id: int, db: db_dependency):
    article = db.get(Article, article_id)
    if not article or article.published_at is None:
        raise HTTPException(status_code=404, detail="Article not found.")
    return article
