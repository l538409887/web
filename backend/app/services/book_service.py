"""书籍业务逻辑。"""
import math
from datetime import datetime, timedelta
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.book import Book, BookCategory
from app.models.user import SysUser

SORT_MAP = {
    "update": Book.last_update_at.desc(),
    "click": Book.click_count.desc(),
    "collect": Book.collect_count.desc(),
    "recommend": Book.recommend_count.desc(),
    "new": Book.created_at.desc(),
    "word": Book.word_count.desc(),
    "subscribe": Book.revenue_coin.desc(),
    "watermelon": Book.watermelon_count.desc(),
    "comment": Book.paragraph_comment_count.desc(),
}


def list_books(
    db: Session,
    *,
    category_id: int | None = None,
    keyword: str | None = None,
    status: int | None = None,
    author_id: int | None = None,
    min_words: int | None = None,
    max_words: int | None = None,
    days: int | None = None,
    sort: str = "update",
    page: int = 1,
    size: int = 20,
) -> tuple[list[Book], int]:
    conditions = [Book.is_online]
    join_author = False

    if category_id:
        conditions.append(Book.category_id == category_id)
    if status is not None:
        conditions.append(Book.status == status)
    if author_id is not None:
        conditions.append(Book.author_id == author_id)
    if min_words is not None:
        conditions.append(Book.word_count >= min_words)
    if max_words is not None:
        conditions.append(Book.word_count < max_words)
    if days:
        conditions.append(Book.last_update_at >= datetime.now() - timedelta(days=days))

    if keyword and keyword.strip():
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(Book.title.like(like), SysUser.nickname.like(like))
        )
        join_author = True
        if sort == "update":
            sort = "click"

    count_stmt = select(func.count()).select_from(Book).where(*conditions)
    if join_author:
        count_stmt = count_stmt.join(SysUser, SysUser.id == Book.author_id)
    total = int(db.scalar(count_stmt) or 0)

    data_stmt = select(Book).where(*conditions)
    if join_author:
        data_stmt = data_stmt.join(SysUser, SysUser.id == Book.author_id)

    order_by = SORT_MAP.get(sort, SORT_MAP["update"])
    data_stmt = (
        data_stmt.order_by(order_by, Book.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = list(db.scalars(data_stmt).all())
    return rows, total


def get_book(db: Session, book_id: int) -> Book | None:
    stmt = select(Book).where(Book.id == book_id, Book.is_online)
    return db.scalars(stmt).first()


def incr_click(db: Session, book_id: int) -> None:
    from app.services import stat_service

    db.execute(
        update(Book).where(Book.id == book_id).values(click_count=Book.click_count + 1)
    )
    # 同时写当日流水，供周榜/月榜聚合
    stat_service.bump(db, book_id, "click")
    db.commit()


def recalc_stats(db: Session, book_id: int) -> None:
    """重算书籍冗余统计字段（章节数 / 字数 / 最新章节）。

    会话配置了 autoflush=False，调用前必须先 flush，
    否则刚改过 status / word_count 的章节不会被这次统计看到。
    """
    from app.models.chapter import BookChapter

    db.flush()

    total_chapters, total_words = db.execute(
        select(
            func.count(BookChapter.id),
            func.coalesce(func.sum(BookChapter.word_count), 0),
        ).where(BookChapter.book_id == book_id, BookChapter.status == 1)
    ).one()

    last = db.scalar(
        select(BookChapter)
        .where(BookChapter.book_id == book_id, BookChapter.status == 1)
        .order_by(BookChapter.chapter_no.desc())
        .limit(1)
    )

    words = int(total_words or 0)
    db.execute(
        update(Book)
        .where(Book.id == book_id)
        .values(
            chapter_count=int(total_chapters or 0),
            word_count=words,
            last_chapter_id=last.id if last else None,
            last_chapter_title=last.title if last else "",
            last_update_at=last.created_at if last else None,
        )
    )

    # 付费作品的整本价随字数变化，必须一起重算（每千字 5 软妹币）
    price = max(1, math.ceil(words * 5 / 1000)) if words else 0
    db.execute(
        update(Book).where(Book.id == book_id, Book.is_paid == 1).values(price_coin=price)
    )


def list_categories(db: Session) -> list[dict]:
    stmt = (
        select(
            BookCategory.id,
            BookCategory.name,
            func.count(Book.id).label("book_count"),
        )
        .outerjoin(
            Book,
            (Book.category_id == BookCategory.id) & (Book.is_online),
        )
        .group_by(BookCategory.id, BookCategory.name, BookCategory.sort)
        .order_by(BookCategory.sort.asc())
    )
    return [
        {"id": row.id, "name": row.name, "book_count": int(row.book_count)}
        for row in db.execute(stmt).all()
    ]