"""书架与阅读进度业务逻辑。"""
from sqlalchemy import func, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.book import Book
from app.models.chapter import BookChapter
from app.models.shelf import ReadingHistory, UserBookshelf


def add_to_shelf(db: Session, user_id: int, book_id: int) -> None:
    book = db.scalar(select(Book.id).where(Book.id == book_id, Book.audit_status == 1))
    if book is None:
        raise BizError(3001, "书籍不存在或已下架")

    exists = db.scalar(
        select(UserBookshelf.id).where(
            UserBookshelf.user_id == user_id, UserBookshelf.book_id == book_id
        )
    )
    if exists:
        raise BizError(4001, "该书籍已在书架中")

    db.add(UserBookshelf(user_id=user_id, book_id=book_id))
    db.execute(
        update(Book).where(Book.id == book_id).values(collect_count=Book.collect_count + 1)
    )
    db.commit()


def remove_from_shelf(db: Session, user_id: int, book_id: int) -> None:
    row = db.scalar(
        select(UserBookshelf).where(
            UserBookshelf.user_id == user_id, UserBookshelf.book_id == book_id
        )
    )
    if row is None:
        return
    db.delete(row)
    db.execute(
        update(Book)
        .where(Book.id == book_id, Book.collect_count > 0)
        .values(collect_count=Book.collect_count - 1)
    )
    db.commit()


def set_top(db: Session, user_id: int, book_id: int, is_top: bool) -> None:
    row = db.scalar(
        select(UserBookshelf).where(
            UserBookshelf.user_id == user_id, UserBookshelf.book_id == book_id
        )
    )
    if row is None:
        raise BizError(1004, "书架中没有这本书")

    if is_top:
        tops = db.scalar(
            select(func.count()).select_from(UserBookshelf).where(
                UserBookshelf.user_id == user_id, UserBookshelf.is_top == 1
            )
        ) or 0
        if tops >= 3 and not row.is_top:
            raise BizError(1001, "最多置顶 3 本")

    row.is_top = 1 if is_top else 0
    db.commit()


def upsert_history(
    db: Session, user_id: int, book_id: int, chapter_id: int, progress: int
) -> None:
    chapter = db.get(BookChapter, chapter_id)
    if chapter is None or chapter.book_id != book_id:
        raise BizError(3002, "章节不存在")

    stmt = mysql_insert(ReadingHistory).values(
        user_id=user_id,
        book_id=book_id,
        chapter_id=chapter_id,
        chapter_no=chapter.chapter_no,
        progress=max(0, min(100, progress)),
        read_count=1,
    )
    stmt = stmt.on_duplicate_key_update(
        chapter_id=stmt.inserted.chapter_id,
        chapter_no=stmt.inserted.chapter_no,
        progress=stmt.inserted.progress,
        read_count=ReadingHistory.read_count + 1,
    )
    db.execute(stmt)
    db.commit()


def _history_map(db: Session, user_id: int, book_ids: list[int]) -> dict[int, ReadingHistory]:
    if not book_ids:
        return {}
    rows = db.scalars(
        select(ReadingHistory).where(
            ReadingHistory.user_id == user_id, ReadingHistory.book_id.in_(book_ids)
        )
    ).all()
    return {row.book_id: row for row in rows}


def list_shelf(db: Session, user_id: int, page: int, size: int) -> tuple[list[dict], int]:
    total = int(
        db.scalar(
            select(func.count()).select_from(UserBookshelf).where(
                UserBookshelf.user_id == user_id
            )
        )
        or 0
    )

    stmt = (
        select(UserBookshelf)
        .where(UserBookshelf.user_id == user_id)
        .order_by(UserBookshelf.is_top.desc(), UserBookshelf.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = list(db.scalars(stmt).all())
    hist = _history_map(db, user_id, [r.book_id for r in rows])

    chapter_ids = [h.chapter_id for h in hist.values()]
    chapters = {}
    if chapter_ids:
        chapters = {
            c.id: c
            for c in db.scalars(
                select(BookChapter).where(BookChapter.id.in_(chapter_ids))
            ).all()
        }

    result = []
    for row in rows:
        h = hist.get(row.book_id)
        last_read = None
        has_update = False
        if h is not None:
            ch = chapters.get(h.chapter_id)
            last_read = {
                "chapter_id": h.chapter_id,
                "chapter_no": h.chapter_no,
                "chapter_title": ch.title if ch else "",
                "progress": h.progress,
                "updated_at": h.updated_at,
            }
            if row.book.last_update_at and h.updated_at:
                has_update = row.book.last_update_at > h.updated_at
        result.append(
            {
                "book": row.book,
                "is_top": bool(row.is_top),
                "last_read": last_read,
                "has_update": has_update,
            }
        )
    return result, total


def list_history(db: Session, user_id: int, limit: int) -> list[dict]:
    rows = list(
        db.scalars(
            select(ReadingHistory)
            .where(ReadingHistory.user_id == user_id)
            .order_by(ReadingHistory.updated_at.desc())
            .limit(limit)
        ).all()
    )
    if not rows:
        return []

    book_ids = [r.book_id for r in rows]
    books = {
        b.id: b
        for b in db.scalars(select(Book).where(Book.id.in_(book_ids))).all()
    }
    chapter_ids = [r.chapter_id for r in rows]
    chapters = {
        c.id: c
        for c in db.scalars(
            select(BookChapter).where(BookChapter.id.in_(chapter_ids))
        ).all()
    }

    result = []
    for row in rows:
        book = books.get(row.book_id)
        chapter = chapters.get(row.chapter_id)
        if book is None:
            continue
        result.append(
            {
                "book": book,
                "chapter": {
                    "id": row.chapter_id,
                    "chapter_no": row.chapter_no,
                    "title": chapter.title if chapter else "",
                },
                "progress": row.progress,
                "updated_at": row.updated_at,
            }
        )
    return result