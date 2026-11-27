"""作者主页与关注接口。"""
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.book import BookCard
from app.services import author_service, book_service

router = APIRouter(prefix="/authors", tags=["作者"])


@router.get("/{author_id}", summary="作者主页信息")
def get_author(
    author_id: int,
    viewer: SysUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    return ok(author_service.get_author(db, author_id, viewer.id if viewer else None))


@router.get("/{author_id}/books", summary="作者的全部作品")
def list_author_books(
    author_id: int,
    page: int = 1,
    size: int = 20,
    sort: str = "update",
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = book_service.list_books(
        db, author_id=author_id, page=page, size=size, sort=sort
    )
    items = [BookCard.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok({"list": items, "total": total, "page": page, "size": size, "pages": pages})


@router.post("/{author_id}/follow", summary="关注作者")
def follow(
    author_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = author_service.follow(db, user.id, author_id)
    logger.bind(business=True).info("AUTHOR_FOLLOW user={} author={}", user.id, author_id)
    return ok(result)


@router.delete("/{author_id}/follow", summary="取消关注")
def unfollow(
    author_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = author_service.unfollow(db, user.id, author_id)
    logger.bind(business=True).info("AUTHOR_UNFOLLOW user={} author={}", user.id, author_id)
    return ok(result)