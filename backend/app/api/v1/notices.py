"""站点公告接口（公开）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.services import notice_service

router = APIRouter(prefix="/notices", tags=["公告"])


@router.get("", summary="首页资讯列表")
def list_notices(limit: int = 6, db: Session = Depends(get_db)):
    limit = min(max(1, limit), 20)
    rows = notice_service.list_public(db, limit)
    return ok(
        [
            {
                "id": row.id,
                "title": row.title,
                "content": row.content,
                "cover": row.cover,
                "category": row.category,
                "is_top": bool(row.is_top),
                "created_at": row.created_at,
            }
            for row in rows
        ]
    )