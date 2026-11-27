"""章节接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.exceptions import BizError
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.chapter import ChapterDetail
from app.services import chapter_service

router = APIRouter(prefix="/chapters", tags=["章节"])


@router.get("/{chapter_id}", summary="章节正文")
def get_chapter(
    chapter_id: int,
    user: SysUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    data = chapter_service.get_chapter_detail(db, chapter_id, user.id if user else None)
    if data is None:
        raise BizError(3002, "章节不存在")
    return ok(ChapterDetail(**data))
