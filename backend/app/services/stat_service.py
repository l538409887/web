"""书籍每日统计：写入与周期聚合（周榜 / 月榜数据源）。

设计：
    - 每次「点击 / 收藏 / 投喂」既更新 book 表的累计字段，也 upsert 到当日流水，
      保证「总榜」和「周/月榜」两套口径都能用
    - 聚合查询按日期区间 SUM，再按可见性过滤（未上架的书不进榜）
"""
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.book import Book
from app.models.stat import BookDailyStat

# 对外指标名 -> 数据库列名
FIELDS = {
    "click": "clicks",
    "collect": "collects",
    "recommend": "recommendations",
}

# 周期 -> 天数（含今天）
PERIOD_DAYS = {"week": 7, "month": 30}

PERIOD_LABELS = {"week": "周榜", "month": "月榜", "all": "总榜"}


def bump(db: Session, book_id: int, metric: str, delta: int = 1) -> None:
    """给某本书当天对应指标加 delta（可为负，最小到 0）。

    只 add 到 session 不 commit，由调用方所在事务统一提交。
    """
    column_name = FIELDS.get(metric)
    if not column_name or not book_id:
        return

    column = getattr(BookDailyStat, column_name)
    today = date.today()

    stmt = insert(BookDailyStat).values(
        book_id=book_id,
        stat_date=today,
        **{column_name: max(0, delta)},
    )
    stmt = stmt.on_duplicate_key_update(
        **{column_name: func.greatest(column + delta, 0)}
    )
    db.execute(stmt)


def period_top(
    db: Session, metric: str = "click", period: str = "week", limit: int = 20
) -> list[dict]:
    """按周期聚合出榜单：[{"book": Book, "value": int}, ...]"""
    column_name = FIELDS.get(metric)
    if not column_name:
        raise BizError(1001, f"metric 只能是 {'/'.join(FIELDS)}")

    days = PERIOD_DAYS.get(period)
    if days is None:
        raise BizError(1001, "period 只能是 week / month")

    column = getattr(BookDailyStat, column_name)
    start = date.today() - timedelta(days=days - 1)
    value_expr = func.coalesce(func.sum(column), 0).label("value")

    rows = db.execute(
        select(BookDailyStat.book_id, value_expr)
        .where(BookDailyStat.stat_date >= start, BookDailyStat.stat_date <= date.today())
        .group_by(BookDailyStat.book_id)
        .order_by(value_expr.desc())
        .limit(limit * 3)
    ).all()

    if not rows:
        return []

    book_ids = [row.book_id for row in rows]
    books = {
        book.id: book
        for book in db.scalars(
            select(Book).where(Book.id.in_(book_ids), Book.is_online)
        ).all()
    }

    result = []
    for row in rows:
        book = books.get(row.book_id)
        if book is None:
            continue
        result.append({"book": book, "value": int(row.value or 0)})
        if len(result) >= limit:
            break
    return result
