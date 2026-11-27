"""站点公告业务。"""
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.notice import SiteNotice, UserNotice

CATEGORIES = ("公告", "活动", "更新")


def list_public(db: Session, limit: int = 6) -> list[SiteNotice]:
    return list(
        db.scalars(
            select(SiteNotice)
            .where(SiteNotice.status == 1)
            .order_by(SiteNotice.is_top.desc(), SiteNotice.created_at.desc(), SiteNotice.id.desc())
            .limit(limit)
        ).all()
    )


def list_all(db: Session, status: int | None = None, page: int = 1, size: int = 20):
    conditions = []
    if status is not None:
        conditions.append(SiteNotice.status == status)

    total = int(db.scalar(select(func.count()).select_from(SiteNotice).where(*conditions)) or 0)
    rows = list(
        db.scalars(
            select(SiteNotice)
            .where(*conditions)
            .order_by(SiteNotice.is_top.desc(), SiteNotice.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def _validate(title: str, category: str) -> tuple[str, str]:
    text = (title or "").strip()
    if not text:
        raise BizError(1001, "标题不能为空")
    if len(text) > 120:
        raise BizError(1001, "标题最多 120 字")
    cat = (category or "公告").strip()
    if cat not in CATEGORIES:
        raise BizError(1001, "分类只能是 公告 / 活动 / 更新")
    return text, cat


def create(db: Session, title: str, content: str, category: str, is_top: bool) -> SiteNotice:
    text, cat = _validate(title, category)
    notice = SiteNotice(
        title=text,
        content=(content or "").strip()[:500],
        category=cat,
        is_top=1 if is_top else 0,
        status=1,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return notice


def update(db: Session, notice_id: int, payload: dict) -> SiteNotice:
    notice = db.get(SiteNotice, notice_id)
    if notice is None:
        raise BizError(1004, "公告不存在")

    if "title" in payload or "category" in payload:
        text, cat = _validate(
            payload.get("title", notice.title), payload.get("category", notice.category)
        )
        notice.title = text
        notice.category = cat
    if "content" in payload:
        notice.content = (payload.get("content") or "").strip()[:500]
    if "is_top" in payload:
        notice.is_top = 1 if payload.get("is_top") else 0
    if "status" in payload:
        notice.status = 1 if payload.get("status") else 0

    db.commit()
    db.refresh(notice)
    return notice


def delete(db: Session, notice_id: int) -> None:
    notice = db.get(SiteNotice, notice_id)
    if notice is None:
        raise BizError(1004, "公告不存在")
    db.delete(notice)
    db.commit()

# ---------------------------------------------------------------
# 站内通知（发给具体用户）
# ---------------------------------------------------------------


def notify(
    db: Session,
    user_id: int,
    notice_type: str,
    title: str,
    content: str = "",
    link: str = "",
) -> None:
    """写入一条站内通知。只 add 不 commit，由调用方所在事务统一提交。"""
    if not user_id:
        return
    db.add(
        UserNotice(
            user_id=user_id,
            type=notice_type,
            title=title[:150],
            content=(content or "")[:500],
            link=link[:200],
            is_read=0,
        )
    )


def list_my_notices(db: Session, user_id: int, page: int = 1, size: int = 10, unread_only: bool = False):
    conditions = [UserNotice.user_id == user_id]
    if unread_only:
        conditions.append(UserNotice.is_read == 0)

    total = int(db.scalar(select(func.count()).select_from(UserNotice).where(*conditions)) or 0)
    rows = list(
        db.scalars(
            select(UserNotice)
            .where(*conditions)
            .order_by(UserNotice.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def unread_count(db: Session, user_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(UserNotice)
            .where(UserNotice.user_id == user_id, UserNotice.is_read == 0)
        )
        or 0
    )


def mark_read(db: Session, user_id: int, notice_id: int) -> None:
    notice = db.get(UserNotice, notice_id)
    if notice is None or notice.user_id != user_id:
        raise BizError(1004, "通知不存在")
    notice.is_read = 1
    db.commit()


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        sa_update(UserNotice)
        .where(UserNotice.user_id == user_id, UserNotice.is_read == 0)
        .values(is_read=1)
    )
    db.commit()
    return int(result.rowcount or 0)