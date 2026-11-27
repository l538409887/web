"""管理后台业务逻辑。"""
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.book import Book, BookCategory
from app.models.chapter import BookChapter
from app.models.comment import BookComment
from app.models.user import SysUser
from app.services import comment_service
from app.services.book_service import recalc_stats
from app.utils.text import count_words, split_chapters


# ---------------- 数据看板 ----------------
def get_stats(db: Session) -> dict:
    today = func.current_date()

    def _count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    return {
        "user_count": _count(SysUser),
        "book_count": _count(Book),
        "chapter_count": _count(BookChapter),
        "comment_count": _count(BookComment),
        "category_count": _count(BookCategory),
        "today_new_users": int(
            db.scalar(select(func.count()).select_from(SysUser).where(SysUser.created_at >= today)) or 0
        ),
        "today_new_books": int(
            db.scalar(select(func.count()).select_from(Book).where(Book.created_at >= today)) or 0
        ),
        "today_new_chapters": int(
            db.scalar(select(func.count()).select_from(BookChapter).where(BookChapter.created_at >= today)) or 0
        ),
        "today_new_comments": int(
            db.scalar(select(func.count()).select_from(BookComment).where(BookComment.created_at >= today)) or 0
        ),
    }


# ---------------- 书籍管理 ----------------
def list_books(
    db: Session,
    *,
    keyword: str | None,
    audit_status: int | None,
    page: int,
    size: int,
) -> tuple[list[Book], int]:
    conditions = []
    join_author = False
    if keyword and keyword.strip():
        like = f"%{keyword.strip()}%"
        conditions.append(Book.title.like(like))
    if audit_status is not None:
        conditions.append(Book.audit_status == audit_status)

    count_stmt = select(func.count()).select_from(Book).where(*conditions)
    data_stmt = select(Book).where(*conditions)
    if join_author:
        count_stmt = count_stmt.join(SysUser, SysUser.id == Book.author_id)
        data_stmt = data_stmt.join(SysUser, SysUser.id == Book.author_id)

    total = int(db.scalar(count_stmt) or 0)
    rows = list(
        db.scalars(
            data_stmt.order_by(Book.id.desc()).offset((page - 1) * size).limit(size)
        ).all()
    )
    return rows, total


def update_book_status(
    db: Session,
    book_id: int,
    audit_status: int | None,
    is_recommend: bool | None,
) -> None:
    book = db.get(Book, book_id)
    if book is None:
        raise BizError(3001, "书籍不存在")

    if audit_status is not None:
        if audit_status not in (0, 1, 2):
            raise BizError(1001, "audit_status 只能是 0/1/2")
        book.audit_status = audit_status
    if is_recommend is not None:
        book.is_recommend = 1 if is_recommend else 0
    db.commit()


def create_book(db: Session, payload) -> Book:
    author = db.get(SysUser, payload.author_id)
    if author is None:
        raise BizError(1001, "作者不存在")
    category = db.get(BookCategory, payload.category_id)
    if category is None:
        raise BizError(1001, "分类不存在")

    book = Book(
        title=payload.title,
        author_id=payload.author_id,
        category_id=payload.category_id,
        intro=payload.intro,
        cover=payload.cover or "",
        status=payload.status,
        audit_status=1,
        is_recommend=1 if payload.is_recommend else 0,
        word_count=0,
        chapter_count=0,
        last_chapter_title="",
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def preview_chapters(db: Session, book_id: int, raw_text: str) -> list[dict]:
    if db.get(Book, book_id) is None:
        raise BizError(3001, "书籍不存在")
    return [
        {"title": title, "word_count": count_words(body or title)}
        for title, body in split_chapters(raw_text)
    ]


def import_chapters(db: Session, book_id: int, raw_text: str) -> dict:
    book = db.get(Book, book_id)
    if book is None:
        raise BizError(3001, "书籍不存在")

    items = split_chapters(raw_text)
    if not items:
        raise BizError(1001, "没有解析到任何章节")

    max_no = int(
        db.scalar(
            select(func.max(BookChapter.chapter_no)).where(BookChapter.book_id == book_id)
        )
        or 0
    )

    created: list[BookChapter] = []
    for offset, (title, body) in enumerate(items, start=1):
        content = body or title
        chapter = BookChapter(
            book_id=book_id,
            chapter_no=max_no + offset,
            title=title[:200],
            content=content,
            word_count=count_words(content),
            status=1,
        )
        db.add(chapter)
        created.append(chapter)

    db.flush()
    recalc_stats(db, book_id)
    db.commit()

    return {
        "imported": len(created),
        "titles": [item.title for item in created],
        "first_chapter_id": created[0].id if created else None,
    }


# ---------------- 用户管理 ----------------
def list_users(
    db: Session,
    *,
    keyword: str | None,
    role: str | None,
    status: int | None,
    page: int,
    size: int,
) -> tuple[list[SysUser], int]:
    conditions = []
    if keyword and keyword.strip():
        like = f"%{keyword.strip()}%"
        conditions.append(SysUser.username.like(like))
    if role:
        conditions.append(SysUser.role == role)
    if status is not None:
        conditions.append(SysUser.status == status)

    total = int(db.scalar(select(func.count()).select_from(SysUser).where(*conditions)) or 0)
    rows = list(
        db.scalars(
            select(SysUser)
            .where(*conditions)
            .order_by(SysUser.id.asc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def update_user(
    db: Session, admin: SysUser, user_id: int, status: int | None, role: str | None
) -> None:
    if user_id == admin.id:
        raise BizError(1001, "不能修改自己的账号状态或角色")

    user = db.get(SysUser, user_id)
    if user is None:
        raise BizError(1004, "用户不存在")

    if status is not None:
        if status not in (0, 1):
            raise BizError(1001, "status 只能是 0/1")
        user.status = status
    if role is not None:
        if role not in ("reader", "author", "admin"):
            raise BizError(1001, "角色只能是 reader / author / admin")
        user.role = role
    db.commit()


# ---------------- 评论管理 ----------------
def list_comments(
    db: Session,
    *,
    book_id: int | None,
    status: int | None,
    page: int,
    size: int,
) -> tuple[list[dict], int]:
    conditions = []
    if book_id:
        conditions.append(BookComment.book_id == book_id)
    if status is not None:
        conditions.append(BookComment.status == status)
    return comment_service.list_with_meta(db, conditions, page, size)

# ---------------- 分类管理 ----------------
def create_category(db: Session, name: str, sort: int) -> BookCategory:
    exists = db.scalar(select(BookCategory.id).where(BookCategory.name == name))
    if exists:
        raise BizError(1001, "分类名已存在")
    category = BookCategory(name=name, sort=sort)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, name: str | None, sort: int | None) -> None:
    category = db.get(BookCategory, category_id)
    if category is None:
        raise BizError(1004, "分类不存在")
    if name and name != category.name:
        if db.scalar(select(BookCategory.id).where(BookCategory.name == name)):
            raise BizError(1001, "分类名已存在")
        category.name = name
    if sort is not None:
        category.sort = sort
    db.commit()


def delete_category(db: Session, category_id: int) -> None:
    category = db.get(BookCategory, category_id)
    if category is None:
        raise BizError(1004, "分类不存在")
    used = int(
        db.scalar(select(func.count()).select_from(Book).where(Book.category_id == category_id)) or 0
    )
    if used > 0:
        raise BizError(1001, f"该分类下还有 {used} 本书，请先迁移")
    db.delete(category)
    db.commit()