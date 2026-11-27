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