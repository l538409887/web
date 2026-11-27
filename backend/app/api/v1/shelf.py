"""书架与阅读进度接口。"""
from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.book import BookCard
from app.schemas.chapter import ChapterBrief
from app.schemas.common import PageResult
from app.schemas.shelf import HistoryItem, LastReadOut, ShelfItem
from app.services import shelf_service

router = APIRouter(tags=["书架"])


class ShelfAddIn(BaseModel):
    book_id: int


class ShelfTopIn(BaseModel):
    is_top: bool


class HistoryIn(BaseModel):
    book_id: int
    chapter_id: int
    progress: int = 0


@router.get("/bookshelf", summary="书架列表")
def list_shelf(
    page: int = 1,
    size: int = 20,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)

    rows, total = shelf_service.list_shelf(db, user.id, page, size)
    items = [
        ShelfItem(
            book=BookCard.model_validate(row["book"]),
            is_top=row["is_top"],
            last_read=LastReadOut(**row["last_read"]) if row["last_read"] else None,
            has_update=row["has_update"],
        )
        for row in rows
    ]
    pages = (total + size - 1) // size
    return ok(
        PageResult[ShelfItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.post("/bookshelf", summary="加入书架")
def add_to_shelf(
    payload: ShelfAddIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shelf_service.add_to_shelf(db, user.id, payload.book_id)
    logger.bind(business=True).info("SHELF_ADD user={} book={}", user.id, payload.book_id)
    return ok({"book_id": payload.book_id, "is_collected": True})


@router.delete("/bookshelf/{book_id}", summary="移出书架")
def remove_from_shelf(
    book_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shelf_service.remove_from_shelf(db, user.id, book_id)
    logger.bind(business=True).info("SHELF_REMOVE user={} book={}", user.id, book_id)
    return ok({"book_id": book_id, "is_collected": False})


@router.put("/bookshelf/{book_id}/top", summary="书架置顶")
def set_top(
    book_id: int,
    payload: ShelfTopIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shelf_service.set_top(db, user.id, book_id, payload.is_top)
    return ok({"book_id": book_id, "is_top": payload.is_top})


@router.get("/history", summary="最近阅读")
def list_history(
    limit: int = 10,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = shelf_service.list_history(db, user.id, min(max(1, limit), 20))
    items = [
        HistoryItem(
            book=BookCard.model_validate(row["book"]),
            chapter=ChapterBrief(**row["chapter"]),
            progress=row["progress"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]
    return ok({"list": items})


@router.post("/history", summary="上报阅读进度")
def upsert_history(
    payload: HistoryIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shelf_service.upsert_history(
        db, user.id, payload.book_id, payload.chapter_id, payload.progress
    )
    return ok({"updated": True})