"""作者中心接口。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.admin import AdminBookItem
from app.schemas.auth import UserOut
from app.schemas.author import (
    AuthorBookIn,
    AuthorBookUpdateIn,
    ChapterIn,
    ChapterItem,
    ChapterUpdateIn,
)
from app.schemas.admin import ChapterImportIn
from app.schemas.common import PageResult
from app.services import author_service

router = APIRouter(prefix="/author", tags=["作者中心"])

AUTHOR = require_role("author", "admin")


@router.post("/apply", summary="申请成为作者（自助升级）")
def apply_author(
    user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    updated = author_service.apply_author(db, user)
    logger.bind(business=True).info("AUTHOR_APPLY user={} role={}", updated.id, updated.role)
    return ok(UserOut.model_validate(updated))


@router.get("/books", summary="我的作品")
def list_my_books(
    page: int = 1,
    size: int = 20,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = author_service.list_my_books(db, user, page, size)
    items = [AdminBookItem.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[AdminBookItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.post("/books", summary="创建作品")
def create_book(
    payload: AuthorBookIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    book = author_service.create_book(db, user, payload)
    logger.bind(business=True).info("BOOK_CREATE author={} book={}", user.id, book.id)
    return ok({"id": book.id, "title": book.title, "audit_status": book.audit_status})


@router.put("/books/{book_id}", summary="编辑作品")
def update_book(
    book_id: int,
    payload: AuthorBookUpdateIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    book = author_service.update_book(db, user, book_id, payload)
    return ok({"id": book.id, "title": book.title, "status": book.status})


@router.get("/books/{book_id}/chapters", summary="作品章节列表（含隐藏）")
def list_chapters(
    book_id: int,
    page: int = 1,
    size: int = 200,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 500)
    rows, total = author_service.list_chapters(db, user, book_id, page, size)
    items = [ChapterItem.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[ChapterItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.post("/books/{book_id}/chapters", summary="新增章节")
def create_chapter(
    book_id: int,
    payload: ChapterIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    chapter = author_service.create_chapter(
        db, user, book_id, payload.title, payload.content
    )
    logger.bind(business=True).info(
        "CHAPTER_PUBLISH author={} book={} chapter={} words={}",
        user.id,
        book_id,
        chapter.id,
        chapter.word_count,
    )
    return ok({"id": chapter.id, "chapter_no": chapter.chapter_no})


@router.post("/books/{book_id}/chapters/preview", summary="分章预览（不落库）")
def preview_chapters(
    book_id: int,
    payload: ChapterImportIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    items = author_service.preview_chapters(db, user, book_id, payload.raw_text)
    return ok({"count": len(items), "items": items})


@router.post("/books/{book_id}/chapters/import", summary="批量分章导入")
def import_chapters(
    book_id: int,
    payload: ChapterImportIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    result = author_service.import_chapters(db, user, book_id, payload.raw_text)
    logger.bind(business=True).info(
        "CHAPTER_IMPORT author={} book={} count={}",
        user.id,
        book_id,
        result["imported"],
    )
    return ok(result)


@router.put("/chapters/{chapter_id}", summary="编辑章节")
def update_chapter(
    chapter_id: int,
    payload: ChapterUpdateIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    chapter = author_service.update_chapter(db, user, chapter_id, payload)
    return ok({"id": chapter.id, "word_count": chapter.word_count})


@router.delete("/chapters/{chapter_id}", summary="删除章节（逻辑删除）")
def delete_chapter(
    chapter_id: int,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    author_service.delete_chapter(db, user, chapter_id)
    logger.bind(business=True).info("CHAPTER_DELETE author={} chapter={}", user.id, chapter_id)
    return ok(None)

@router.get("/chapters/{chapter_id}", summary="章节详情（含正文）")
def get_chapter(
    chapter_id: int,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    chapter = author_service.get_chapter(db, user, chapter_id)
    return ok(
        {
            "id": chapter.id,
            "book_id": chapter.book_id,
            "chapter_no": chapter.chapter_no,
            "title": chapter.title,
            "content": chapter.content,
            "word_count": chapter.word_count,
            "status": chapter.status,
        }
    )

class PaidIn(BaseModel):
    is_paid: bool


@router.put("/books/{book_id}/paid", summary="开启 / 关闭付费")
def set_paid(
    book_id: int,
    payload: PaidIn,
    user: SysUser = Depends(AUTHOR),
    db: Session = Depends(get_db),
):
    from app.services import interaction_service

    book = interaction_service.set_paid(db, user, book_id, payload.is_paid)
    logger.bind(business=True).info(
        "BOOK_PAID author={} book={} is_paid={} price={}",
        user.id,
        book_id,
        book.is_paid,
        book.price_coin,
    )
    return ok({"book_id": book.id, "is_paid": bool(book.is_paid), "price_coin": book.price_coin})