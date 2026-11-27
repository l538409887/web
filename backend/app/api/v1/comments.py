"""评论接口：书评、章评、回复。"""
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.comment import BookComment
from app.models.user import SysUser
from app.schemas.auth import UserBriefOut
from app.schemas.comment import CommentCreateIn, CommentOut
from app.schemas.common import PageResult
from app.services import comment_service

router = APIRouter(tags=["评论"])


def _to_out(comment: BookComment, replies: list[BookComment]) -> CommentOut:
    return CommentOut(
        id=comment.id,
        user=UserBriefOut.model_validate(comment.user),
        content=comment.content,
        like_count=comment.like_count,
        created_at=comment.created_at,
        parent_id=comment.parent_id,
        replies=[
            CommentOut(
                id=item.id,
                user=UserBriefOut.model_validate(item.user),
                content=item.content,
                like_count=item.like_count,
                created_at=item.created_at,
                parent_id=item.parent_id,
                replies=[],
            )
            for item in replies
        ],
    )


def _pack(roots, reply_map, total, page, size):
    items = [_to_out(root, reply_map.get(root.id, [])) for root in roots]
    pages = (total + size - 1) // size
    return PageResult[CommentOut](
        list=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/books/{book_id}/comments", summary="书评列表")
def list_book_comments(
    book_id: int,
    page: int = 1,
    size: int = 20,
    sort: str = "latest",
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    roots, reply_map, total = comment_service.list_book_comments(
        db, book_id, page, size, sort
    )
    return ok(_pack(roots, reply_map, total, page, size))


@router.get("/chapters/{chapter_id}/comments", summary="章评列表")
def list_chapter_comments(
    chapter_id: int,
    page: int = 1,
    size: int = 20,
    sort: str = "latest",
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    roots, reply_map, total = comment_service.list_chapter_comments(
        db, chapter_id, page, size, sort
    )
    return ok(_pack(roots, reply_map, total, page, size))


@router.post("/comments", summary="发表评论 / 回复")
def create_comment(
    payload: CommentCreateIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = comment_service.create_comment(db, user, payload)
    logger.bind(business=True).info(
        "COMMENT_CREATE user={} comment={} book={} chapter={}",
        user.id,
        comment.id,
        comment.book_id,
        comment.chapter_id,
    )
    return ok(_to_out(comment, []))


@router.delete("/comments/{comment_id}", summary="删除自己的评论")
def delete_comment(
    comment_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment_service.delete_comment(db, user, comment_id)
    logger.bind(business=True).info(
        "COMMENT_DELETE user={} comment={}", user.id, comment_id
    )
    return ok(None)