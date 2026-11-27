"""用户中心接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.comment import MyCommentItem
from app.schemas.common import PageResult
from app.services import comment_service, interaction_service

router = APIRouter(prefix="/user", tags=["用户中心"])


@router.get("/comments", summary="我的评论")
def my_comments(
    page: int = 1,
    size: int = 20,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = comment_service.list_my_comments(db, user.id, page, size)
    items = [MyCommentItem(**row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[MyCommentItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.get("/paragraph-comments", summary="我的间贴动态")
def my_paragraph_comments(
    page: int = 1,
    size: int = 10,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    items, total = interaction_service.my_paragraph_comments(db, user.id, page, size)
    pages = (total + size - 1) // size
    return ok(
        {
            "list": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }
    )


@router.get("/follows", summary="我关注的作者")
def my_follows(
    page: int = 1,
    size: int = 12,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import author_service

    page = max(1, page)
    size = min(max(1, size), 50)
    items, total = author_service.my_follows(db, user.id, page, size)
    pages = (total + size - 1) // size
    return ok({"list": items, "total": total, "page": page, "size": size, "pages": pages})


@router.get("/notices", summary="我的站内通知")
def my_notices(
    page: int = 1,
    size: int = 10,
    unread_only: bool = False,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import notice_service

    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = notice_service.list_my_notices(db, user.id, page, size, unread_only)
    pages = (total + size - 1) // size
    return ok(
        {
            "list": [
                {
                    "id": r.id,
                    "type": r.type,
                    "title": r.title,
                    "content": r.content,
                    "link": r.link,
                    "is_read": bool(r.is_read),
                    "created_at": r.created_at,
                }
                for r in rows
            ],
            "total": total,
            "unread": notice_service.unread_count(db, user.id),
            "page": page,
            "size": size,
            "pages": pages,
        }
    )


@router.get("/notices/unread-count", summary="未读通知数")
def my_unread_count(
    user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.services import notice_service

    return ok({"unread": notice_service.unread_count(db, user.id)})


@router.put("/notices/{notice_id}/read", summary="标记单条已读")
def read_notice(
    notice_id: int,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import notice_service

    notice_service.mark_read(db, user.id, notice_id)
    return ok({"unread": notice_service.unread_count(db, user.id)})


@router.put("/notices/read-all", summary="全部标记已读")
def read_all_notices(
    user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.services import notice_service

    count = notice_service.mark_all_read(db, user.id)
    return ok({"updated": count, "unread": 0})