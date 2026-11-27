"""首页聚合业务逻辑。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.services import book_service

RANK_MAP = {
    "click": Book.click_count.desc(),
    "collect": Book.collect_count.desc(),
    "recommend": Book.recommend_count.desc(),
    "watermelon": Book.watermelon_count.desc(),
    "subscribe": Book.revenue_coin.desc(),
    "comment": Book.paragraph_comment_count.desc(),
    "new": Book.created_at.desc(),
}

# 首页三个书区
SECTION_SIZE = {
    "featured": 4,   # 好书精选：头部轮展
    "choicest": 12,  # 精品力荐：3 张横卡 + 8 张封面网格
    "rising": 6,     # 新秀小说：最新上架
}


def _top(db: Session, key: str, limit: int = 10) -> list[Book]:
    stmt = (
        select(Book)
        .where(Book.audit_status == 1)
        .order_by(RANK_MAP.get(key, RANK_MAP["click"]), Book.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _section(db: Session, order, limit: int, exclude: set[int] | None = None) -> list[Book]:
    stmt = select(Book).where(Book.audit_status == 1).order_by(order, Book.id.desc())
    rows = list(db.scalars(stmt.limit(limit + (len(exclude) if exclude else 0))).all())
    if exclude:
        rows = [b for b in rows if b.id not in exclude]
    return rows[:limit]


def get_home(db: Session) -> dict:
    banners = list(
        db.scalars(
            select(Book)
            .where(Book.audit_status == 1, Book.is_recommend == 1)
            .order_by(Book.click_count.desc())
            .limit(3)
        ).all()
    )
    latest = list(
        db.scalars(
            select(Book)
            .where(Book.audit_status == 1)
            .order_by(Book.last_update_at.desc())
            .limit(12)
        ).all()
    )

    featured = _section(db, Book.click_count.desc(), SECTION_SIZE["featured"])
    featured_ids = {b.id for b in featured}
    choicest = _section(db, Book.collect_count.desc(), SECTION_SIZE["choicest"], featured_ids)
    choicest_ids = featured_ids | {b.id for b in choicest}
    rising = _section(db, Book.created_at.desc(), SECTION_SIZE["rising"], choicest_ids)

    return {
        "banners": banners,
        "categories": book_service.list_categories(db),
        "ranks": {key: _top(db, key, 10) for key in RANK_MAP},
        "latest": latest,
        "sections": {
            "featured": featured,
            "choicest": choicest,
            "rising": rising,
        },
    }
