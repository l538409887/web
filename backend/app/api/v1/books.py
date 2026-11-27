"""书籍与分类接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.exceptions import BizError
from app.core.response import ok
from app.models.shelf import UserBookshelf
from app.models.user import SysUser
from app.schemas.book import BookCard, BookDetail
from app.schemas.chapter import ChapterBrief
from app.schemas.common import PageResult
from app.services import book_service, chapter_service, interaction_service

router = APIRouter(prefix="/books", tags=["书籍"])


@router.get("", summary="书库列表 / 搜索 / 筛选")
def list_books(
    category_id: int | None = None,
    keyword: str | None = None,
    status: int | None = None,
    min_words: int | None = None,
    max_words: int | None = None,
    days: int | None = None,
    sort: str = "update",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)

    rows, total = book_service.list_books(
        db,
        category_id=category_id,
        keyword=keyword,
        status=status,
        min_words=min_words,
        max_words=max_words,
        days=days,
        sort=sort,
        page=page,
        size=size,
    )
    items = [BookCard.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[BookCard](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.get("/{book_id}", summary="书籍详情（可选登录，返回是否已收藏）")
def get_book(
    book_id: int,
    user: SysUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    book = book_service.get_book(db, book_id)
    if book is None:
        raise BizError(3001, "书籍不存在或已下架")

    detail = BookDetail.model_validate(book)

    if user is not None:
        detail.is_purchased = interaction_service.is_purchased(db, user.id, book_id)
        detail.is_collected = bool(
            db.scalar(
                select(UserBookshelf.id).where(
                    UserBookshelf.user_id == user.id,
                    UserBookshelf.book_id == book_id,
                )
            )
        )

    book_service.incr_click(db, book_id)
    return ok(detail)


@router.get("/{book_id}/chapters", summary="章节目录")
def list_chapters(
    book_id: int,
    page: int = 1,
    size: int = 500,
    order: str = "asc",
    user: SysUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 500)

    rows, total = chapter_service.list_chapters(
        db, book_id, page=page, size=size, order=order
    )
    items = [ChapterBrief.model_validate(row) for row in rows]

    locks = interaction_service.chapter_locks(db, user.id if user else None, book_id, rows)
    for item in items:
        info = locks.get(item.id)
        if info:
            item.locked = info["locked"]
            item.price_coin = info["price_coin"]
    pages = (total + size - 1) // size
    return ok(
        PageResult[ChapterBrief](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )