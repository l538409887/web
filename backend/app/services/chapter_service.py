"""章节业务逻辑。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import BookChapter


def list_chapters(
    db: Session, book_id: int, *, page: int = 1, size: int = 500, order: str = "asc"
) -> tuple[list[BookChapter], int]:
    base = select(BookChapter).where(
        BookChapter.book_id == book_id, BookChapter.is_visible
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    order_by = (
        BookChapter.chapter_no.asc() if order == "asc" else BookChapter.chapter_no.desc()
    )
    stmt = base.order_by(order_by).offset((page - 1) * size).limit(size)
    return list(db.scalars(stmt).all()), int(total)


def get_chapter_detail(db: Session, chapter_id: int, user_id: int | None = None) -> dict | None:
    chapter = db.get(BookChapter, chapter_id)
    if chapter is None or not chapter.is_visible:
        return None

    book = db.get(Book, chapter.book_id)
    if book is None or not book.is_online:
        return None

    from app.services.interaction_service import calc_chapter_price, can_read_chapter

    if not can_read_chapter(db, user_id, book, chapter):
        return {
            "id": chapter.id,
            "book_id": chapter.book_id,
            "book_title": book.title,
            "chapter_no": chapter.chapter_no,
            "title": chapter.title,
            "content": "",
            "word_count": chapter.word_count,
            "prev_id": None,
            "next_id": None,
            "is_collected": False,
            "locked": True,
            "price_coin": book.price_coin,
            "chapter_price": calc_chapter_price(chapter.word_count),
        }

    prev_id = db.scalar(
        select(BookChapter.id)
        .where(
            BookChapter.book_id == chapter.book_id,
            BookChapter.is_visible,
            BookChapter.chapter_no < chapter.chapter_no,
        )
        .order_by(BookChapter.chapter_no.desc())
        .limit(1)
    )
    next_id = db.scalar(
        select(BookChapter.id)
        .where(
            BookChapter.book_id == chapter.book_id,
            BookChapter.is_visible,
            BookChapter.chapter_no > chapter.chapter_no,
        )
        .order_by(BookChapter.chapter_no.asc())
        .limit(1)
    )

    return {
        "id": chapter.id,
        "book_id": chapter.book_id,
        "book_title": book.title,
        "chapter_no": chapter.chapter_no,
        "title": chapter.title,
        "content": chapter.content,
        "word_count": chapter.word_count,
        "prev_id": prev_id,
        "next_id": next_id,
        "is_collected": False,
    }