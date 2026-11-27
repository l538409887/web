"""付费购买、投喂西瓜、间贴接口。"""
from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.services import interaction_service

router = APIRouter(tags=["互动"])


class ChaptersIn(BaseModel):
    chapter_ids: list[int] = Field(min_length=1, max_length=200)


class FeedIn(BaseModel):
    count: int = Field(default=1, ge=1, le=99)


class ParagraphIn(BaseModel):
    book_id: int = 0
    chapter_id: int = 0
    paragraph_index: int = Field(default=0, ge=0)
    content: str = Field(min_length=1, max_length=300)
    parent_id: int | None = None


class ReactIn(BaseModel):
    reaction: int = Field(ge=1, le=3)


@router.post("/books/{book_id}/purchase", summary="购买付费作品")
def purchase(
    book_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = interaction_service.buy_book(db, user.id, book_id)
    logger.bind(business=True).info(
        "BOOK_PURCHASE user={} book={} coin={}", user.id, book_id, result["coin"]
    )
    return ok(result)


@router.post("/books/{book_id}/purchase-chapters", summary="按章购买（支持批量）")
def purchase_chapters(
    book_id: int,
    payload: ChaptersIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = interaction_service.buy_chapters(db, user.id, book_id, payload.chapter_ids)
    logger.bind(business=True).info(
        "CHAPTER_PURCHASE user={} book={} count={} coin={}",
        user.id,
        book_id,
        result["count"],
        result["coin"],
    )
    return ok(result)


@router.post("/books/{book_id}/feed-watermelon", summary="投喂西瓜")
def feed_watermelon(
    book_id: int,
    payload: FeedIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = interaction_service.feed_watermelon(db, user.id, book_id, payload.count)
    logger.bind(business=True).info(
        "FEED_WATERMELON user={} book={} count={}", user.id, book_id, payload.count
    )
    return ok(result)


@router.get("/chapters/{chapter_id}/paragraph-comments", summary="本章间贴（按段落分组）")
def list_paragraph_comments(chapter_id: int, db: Session = Depends(get_db)):
    return ok(interaction_service.list_paragraph_comments(db, chapter_id))


@router.post("/paragraph-comments", summary="发表间贴")
def add_paragraph_comment(
    payload: ParagraphIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = interaction_service.add_paragraph_comment(
        db,
        user,
        payload.book_id,
        payload.chapter_id,
        payload.paragraph_index,
        payload.content,
        payload.parent_id,
    )
    logger.bind(business=True).info(
        "PARAGRAPH_COMMENT user={} comment={} chapter={}",
        user.id,
        comment.id,
        payload.chapter_id,
    )
    return ok({"id": comment.id, "paragraph_index": comment.paragraph_index})


@router.post("/paragraph-comments/{comment_id}/react", summary="赞 / 踩 / 举报")
def react(
    comment_id: int,
    payload: ReactIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(
        interaction_service.react_paragraph_comment(db, user, comment_id, payload.reaction)
    )


@router.delete("/paragraph-comments/{comment_id}", summary="删除自己的间贴")
def delete_paragraph_comment(
    comment_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interaction_service.hide_paragraph_comment(db, user, comment_id)
    return ok(None)