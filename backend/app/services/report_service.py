"""内容举报业务：举报创建、后台队列、处理动作。"""
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.chapter import BookChapter
from app.models.comment import BookComment
from app.models.interaction import ParagraphComment
from app.models.report import (
    TARGET_BOOK_COMMENT,
    TARGET_PARAGRAPH_COMMENT,
    ContentReport,
)
from app.models.user import SysUser

ALLOWED_REASONS = ("广告引流", "辱骂攻击", "违法违规", "色情低俗", "侵权抄袭", "其他")
TARGET_LABEL = {
    TARGET_BOOK_COMMENT: "书评",
    TARGET_PARAGRAPH_COMMENT: "间贴",
}


# ---------------------------------------------------------------
# 举报
# ---------------------------------------------------------------


def _load_target(db: Session, target_type: str, target_id: int):
    if target_type == TARGET_BOOK_COMMENT:
        return db.get(BookComment, target_id)
    if target_type == TARGET_PARAGRAPH_COMMENT:
        return db.get(ParagraphComment, target_id)
    raise BizError(1001, "不支持的举报对象类型")


def create_report(
    db: Session,
    user_id: int,
    target_type: str,
    target_id: int,
    reason: str,
    detail: str = "",
) -> dict:
    if target_type not in TARGET_LABEL:
        raise BizError(1001, "不支持的举报对象类型")

    target = _load_target(db, target_type, target_id)
    if target is None:
        raise BizError(1004, "被举报的内容不存在")
    if target.user_id == user_id:
        raise BizError(1001, "不能举报自己发布的内容")
    if getattr(target, "status", 1) != 1:
        raise BizError(1001, "该内容已被处理")

    reason_text = (reason or "").strip()
    if reason_text not in ALLOWED_REASONS:
        raise BizError(1001, "请选择有效的举报理由")

    report = ContentReport(
        target_type=target_type,
        target_id=target_id,
        reporter_id=user_id,
        reason=reason_text,
        detail=(detail or "").strip()[:300],
        status=0,
    )
    db.add(report)

    if target_type == TARGET_PARAGRAPH_COMMENT:
        db.execute(
            update(ParagraphComment)
            .where(ParagraphComment.id == target_id)
            .values(report_count=ParagraphComment.report_count + 1)
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError(1001, "你已经举报过这条内容了")

    pending = int(
        db.scalar(
            select(func.count())
            .select_from(ContentReport)
            .where(
                ContentReport.target_type == target_type,
                ContentReport.target_id == target_id,
                ContentReport.status == 0,
            )
        )
        or 0
    )
    return {"id": report.id, "pending_reports": pending}


# ---------------------------------------------------------------
# 后台队列
# ---------------------------------------------------------------


def list_reports(
    db: Session,
    *,
    status: int | None = 0,
    target_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    conditions = []
    if status is not None:
        conditions.append(ContentReport.status == status)
    if target_type:
        conditions.append(ContentReport.target_type == target_type)

    total = int(
        db.scalar(select(func.count()).select_from(ContentReport).where(*conditions)) or 0
    )
    rows = list(
        db.scalars(
            select(ContentReport)
            .where(*conditions)
            .order_by(ContentReport.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    # 批量取被举报内容与上下文，避免 N+1
    comment_ids = [r.target_id for r in rows if r.target_type == TARGET_BOOK_COMMENT]
    para_ids = [r.target_id for r in rows if r.target_type == TARGET_PARAGRAPH_COMMENT]

    comments = (
        {c.id: c for c in db.scalars(select(BookComment).where(BookComment.id.in_(comment_ids))).all()}
        if comment_ids
        else {}
    )
    paras = (
        {
            p.id: p
            for p in db.scalars(
                select(ParagraphComment).where(ParagraphComment.id.in_(para_ids))
            ).all()
        }
        if para_ids
        else {}
    )

    reporter_ids = {r.reporter_id for r in rows}
    reporters = (
        {u.id: u for u in db.scalars(select(SysUser).where(SysUser.id.in_(reporter_ids))).all()}
        if reporter_ids
        else {}
    )

    items = []
    for row in rows:
        target = comments.get(row.target_id) or paras.get(row.target_id)
        reporter = reporters.get(row.reporter_id)
        items.append(
            {
                "id": row.id,
                "target_type": row.target_type,
                "target_type_label": TARGET_LABEL.get(row.target_type, row.target_type),
                "target_id": row.target_id,
                "reason": row.reason,
                "detail": row.detail,
                "status": row.status,
                "created_at": row.created_at,
                "handled_at": row.handled_at,
                "reporter": {
                    "id": row.reporter_id,
                    "nickname": reporter.nickname if reporter else "",
                    "username": reporter.username if reporter else "",
                },
                "target": {
                    "content": getattr(target, "content", ""),
                    "status": getattr(target, "status", 0),
                    "user_id": getattr(target, "user_id", 0),
                    "book_id": getattr(target, "book_id", 0),
                    "chapter_id": getattr(target, "chapter_id", None),
                    "paragraph_index": getattr(target, "paragraph_index", None),
                },
            }
        )

    # 补充书名与章节名
    book_ids = {item["target"]["book_id"] for item in items if item["target"]["book_id"]}
    chapter_ids = {item["target"]["chapter_id"] for item in items if item["target"]["chapter_id"]}
    from app.models.book import Book

    books = (
        {b.id: b.title for b in db.scalars(select(Book).where(Book.id.in_(book_ids))).all()}
        if book_ids
        else {}
    )
    chapters = (
        {
            c.id: c.title
            for c in db.scalars(select(BookChapter).where(BookChapter.id.in_(chapter_ids))).all()
        }
        if chapter_ids
        else {}
    )
    for item in items:
        item["target"]["book_title"] = books.get(item["target"]["book_id"], "")
        item["target"]["chapter_title"] = (
            chapters.get(item["target"]["chapter_id"], "") if item["target"]["chapter_id"] else ""
        )

    return items, total


def handle_report(db: Session, admin_id: int, report_id: int, action: str) -> dict:
    """action: ignore 忽略举报 / hide 隐藏内容并处理。"""
    if action not in ("ignore", "hide"):
        raise BizError(1001, "action 只能是 ignore / hide")

    report = db.get(ContentReport, report_id)
    if report is None:
        raise BizError(1004, "举报记录不存在")
    if report.status != 0:
        raise BizError(1001, "该举报已处理")

    target_type = report.target_type
    target_id = report.target_id

    if action == "hide":
        if target_type == TARGET_BOOK_COMMENT:
            from app.services import admin_service

            admin_service.update_comment_status(db, target_id, 0)
        else:
            from app.services import interaction_service

            interaction_service.set_paragraph_status(db, target_id, 0)

    now = datetime.now()
    new_status = 2 if action == "hide" else 1

    # 同一目标的其他待处理举报一并结案，避免管理员重复处理
    db.execute(
        update(ContentReport)
        .where(
            ContentReport.target_type == target_type,
            ContentReport.target_id == target_id,
            ContentReport.status == 0,
        )
        .values(status=new_status, handled_by=admin_id, handled_at=now)
    )
    db.commit()

    return {"report_id": report.id, "status": new_status, "action": action}
