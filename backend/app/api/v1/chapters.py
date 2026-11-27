"""章节接口。"""
from fastapi import APIRouter, Depends, Request, Response
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.core.exceptions import BizError
from app.core.ratelimit import RateLimiter, blocked_response, client_ip
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.chapter import ChapterDetail
from app.services import chapter_service

router = APIRouter(prefix="/chapters", tags=["章节"])

# 按用户维度的正文读取限流：同一账号每分钟最多 40 章，防"买一本批量导出"
_user_chapter_limiter = RateLimiter(rate_per_minute=40, capacity=40)


@router.get("/{chapter_id}", summary="章节正文")
def get_chapter(
    chapter_id: int,
    request: Request,
    response: Response,
    user: SysUser | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    # 登录用户额外按账号限流（IP 维度已由中间件负责）
    if user is not None and not _user_chapter_limiter.allow(f"user:{user.id}"):
        logger.warning("CHAPTER_USER_LIMIT user={} chapter={}", user.id, chapter_id)
        return blocked_response("翻页太快了，请稍后再试", getattr(request.state, "trace_id", "-"))

    data = chapter_service.get_chapter_detail(db, chapter_id, user.id if user else None)
    if data is None:
        raise BizError(3002, "章节不存在")

    # 付费章节：禁止中间层缓存，避免被代理/CDN 留存
    if data.get("is_paid"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"

        # 审计：记录谁在什么 IP 读了付费章节，便于发现异常批量读取
        logger.bind(business=True).info(
            "PAID_READ user={} book={} chapter={} ip={}",
            user.id if user else 0,
            data["book_id"],
            chapter_id,
            client_ip(request),
        )

    return ok(ChapterDetail(**data))