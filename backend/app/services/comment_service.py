"""评论业务逻辑：书评 / 章评 / 一层回复。"""
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.book import Book
from app.models.chapter import BookChapter
from app.models.comment import BookComment
from app.models.user import SysUser


def _query(
    db: Session,
    conditions: list,
    page: int,
    size: int,
    sort: str,
) -> tuple[list[BookComment], dict[int, list[BookComment]], int]:
    root_conditions = [*conditions, BookComment.parent_id.is_(None), BookComment.status == 1]

    total = int(
        db.scalar(
            select(func.count()).select_from(BookComment).where(*root_conditions)
        )
        or 0
    )

    if sort == "hot":
        order_by = (BookComment.like_count.desc(), BookComment.created_at.desc())
    else:
        order_by = (BookComment.created_at.desc(),)

    roots = list(
        db.scalars(
            select(BookComment)
            .where(*root_conditions)
            .order_by(*order_by)
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    reply_map: dict[int, list[BookComment]] = {}
    if roots:
        root_ids = [item.id for item in roots]
        replies = db.scalars(
            select(BookComment)
            .where(BookComment.parent_id.in_(root_ids), BookComment.status == 1)
            .order_by(BookComment.created_at.asc())
        ).all()
        for reply in replies:
            reply_map.setdefault(reply.parent_id, []).append(reply)

    return roots, reply_map, total


def list_book_comments(
    db: Session, book_id: int, page: int, size: int, sort: str = "latest"
):
    return _query(
        db,
        [BookComment.book_id == book_id, BookComment.chapter_id.is_(None)],
        page,
        size,
        sort,
    )


def list_chapter_comments(
    db: Session, chapter_id: int, page: int, size: int, sort: str = "latest"
):
    return _query(db, [BookComment.chapter_id == chapter_id], page, size, sort)


def list_with_meta(
    db: Session, conditions: list, page: int, size: int
) -> tuple[list[dict], int]:
    """分页查询评论，并附带书名、章节标题（供后台与用户中心复用）。"""
    total = int(
        db.scalar(select(func.count()).select_from(BookComment).where(*conditions)) or 0
    )
    rows = list(
        db.scalars(
            select(BookComment)
            .where(*conditions)
            .order_by(BookComment.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    book_ids = {row.book_id for row in rows}
    books = (
        {item.id: item.title for item in db.scalars(select(Book).where(Book.id.in_(book_ids))).all()}
        if book_ids
        else {}
    )

    chapter_ids = {row.chapter_id for row in rows if row.chapter_id}
    chapters = (
        {
            item.id: item.title
            for item in db.scalars(select(BookChapter).where(BookChapter.id.in_(chapter_ids))).all()
        }
        if chapter_ids
        else {}
    )

    items = []
    for row in rows:
        items.append(
            {
                "id": row.id,
                "book_id": row.book_id,
                "book_title": books.get(row.book_id, ""),
                "chapter_id": row.chapter_id,
                "chapter_title": chapters.get(row.chapter_id, "") if row.chapter_id else "",
                "user": row.user,
                "content": row.content,
                "like_count": row.like_count,
                "status": row.status,
                "created_at": row.created_at,
            }
        )
    return items, total


def list_my_comments(
    db: Session, user_id: int, page: int, size: int
) -> tuple[list[dict], int]:
    return list_with_meta(db, [BookComment.user_id == user_id], page, size)


def create_comment(db: Session, user: SysUser, data) -> BookComment:
    book = db.scalar(select(Book.id).where(Book.id == data.book_id, Book.is_online))
    if book is None:
        raise BizError(3001, "书籍不存在或已下架")

    chapter_id = data.chapter_id
    if chapter_id is not None:
        chapter = db.get(BookChapter, chapter_id)
        if chapter is None or chapter.book_id != data.book_id:
            raise BizError(3002, "章节不存在")

    if data.parent_id is not None:
        parent = db.get(BookComment, data.parent_id)
        if parent is None or parent.status != 1:
            raise BizError(1004, "要回复的评论不存在")
        if parent.parent_id is not None:
            raise BizError(1001, "只支持一层回复")
        if parent.book_id != data.book_id:
            raise BizError(1001, "评论不属于该书籍")
        chapter_id = parent.chapter_id

    comment = BookComment(
        book_id=data.book_id,
        chapter_id=chapter_id,
        user_id=user.id,
        parent_id=data.parent_id,
        content=data.content,
        status=1,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, user: SysUser, comment_id: int) -> None:
    comment = db.get(BookComment, comment_id)
    if comment is None or comment.status == 2:
        raise BizError(1004, "评论不存在")

    if comment.user_id != user.id and user.role != "admin":
        raise BizError(5002, "只能删除自己的评论")

    comment.status = 2
    if comment.parent_id is None:
        db.execute(
            update(BookComment)
            .where(BookComment.parent_id == comment.id)
            .values(status=2)
        )
    db.commit()