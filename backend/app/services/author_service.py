"""作者中心业务：作品与章节管理 + 作者主页与关注。

注意：本文件同时承载「作者端后台」（作品/章节 CRUD）与
「读者端作者主页」（资料/关注），两者都属于作者域，故合并在一个模块。
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.core.state import (
    AUDIT_APPROVED,
    AUDIT_DRAFT,
    AUDIT_PENDING,
    CHAPTER_PENDING,
    SHELF_OFFLINE,
    SHELF_ONLINE,
    SHELF_PENDING,
)
from app.models.book import Book, BookCategory
from app.models.chapter import BookChapter
from app.models.follow import AuthorFollow
from app.models.user import SysUser
from app.services import book_service
from app.utils.text import count_words, split_chapters

# ---------------------------------------------------------------
# 作者身份
# ---------------------------------------------------------------


def apply_author(db: Session, user: SysUser) -> SysUser:
    """读者自助升级为作者。"""
    if user.role in ("author", "admin"):
        raise BizError(1001, "你已经是作者了")
    user.role = "author"
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------
# 作品
# ---------------------------------------------------------------


def _own_book(db: Session, user: SysUser, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise BizError(3001, "作品不存在")
    if book.author_id != user.id and user.role != "admin":
        raise BizError(6001, "只能管理自己的作品")
    return book


def _check_category(db: Session, category_id: int) -> None:
    if db.get(BookCategory, category_id) is None:
        raise BizError(3001, "分类不存在")


def list_my_books(db: Session, user: SysUser, page: int = 1, size: int = 20):
    condition = Book.author_id == user.id
    total = int(db.scalar(select(func.count()).select_from(Book).where(condition)) or 0)
    rows = list(
        db.scalars(
            select(Book)
            .where(condition)
            .order_by(Book.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def create_book(db: Session, user: SysUser, payload) -> Book:
    _check_category(db, payload.category_id)

    book = Book(
        title=payload.title.strip(),
        author_id=user.id,
        category_id=payload.category_id,
        intro=payload.intro.strip(),
        cover=payload.cover or "",
        status=payload.status,
        audit_status=AUDIT_DRAFT,
        shelf_status=SHELF_OFFLINE,
        word_count=0,
        chapter_count=0,
        click_count=0,
        collect_count=0,
        recommend_count=0,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, user: SysUser, book_id: int, payload) -> Book:
    book = _own_book(db, user, book_id)

    if payload.category_id is not None:
        _check_category(db, payload.category_id)
        book.category_id = payload.category_id
    if payload.title is not None:
        book.title = payload.title.strip()
    if payload.intro is not None:
        book.intro = payload.intro.strip()
    if payload.cover is not None:
        book.cover = payload.cover
    if payload.status is not None:
        book.status = payload.status

    db.commit()
    db.refresh(book)
    return book


def submit_book(db: Session, user: SysUser, book_id: int) -> Book:
    """提交审核：草稿 / 未通过 -> 待审核。"""
    book = _own_book(db, user, book_id)
    if book.audit_status == AUDIT_PENDING:
        raise BizError(1001, "作品已在审核中，请等待审核结果")
    if book.audit_status == AUDIT_APPROVED:
        raise BizError(1001, "作品已通过审核，无需重复提交")
    book.audit_status = AUDIT_PENDING
    db.commit()
    db.refresh(book)
    return book


def apply_shelf(db: Session, user: SysUser, book_id: int) -> Book:
    """申请上架：必须先通过内容审核。"""
    book = _own_book(db, user, book_id)
    if book.audit_status != AUDIT_APPROVED:
        raise BizError(1001, "请先通过内容审核，再申请上架")
    if book.shelf_status == SHELF_ONLINE:
        raise BizError(1001, "作品已上架")
    if book.shelf_status == SHELF_PENDING:
        raise BizError(1001, "上架申请审核中，请等待结果")
    book.shelf_status = SHELF_PENDING
    db.commit()
    db.refresh(book)
    return book


# ---------------------------------------------------------------
# 章节
# ---------------------------------------------------------------


def _own_chapter(db: Session, user: SysUser, chapter_id: int) -> BookChapter:
    chapter = db.get(BookChapter, chapter_id)
    if chapter is None:
        raise BizError(3002, "章节不存在")
    _own_book(db, user, chapter.book_id)
    return chapter


def list_chapters(db: Session, user: SysUser, book_id: int, page: int = 1, size: int = 200):
    _own_book(db, user, book_id)
    condition = BookChapter.book_id == book_id
    total = int(
        db.scalar(select(func.count()).select_from(BookChapter).where(condition)) or 0
    )
    rows = list(
        db.scalars(
            select(BookChapter)
            .where(condition)
            .order_by(BookChapter.chapter_no.asc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def get_chapter(db: Session, user: SysUser, chapter_id: int) -> BookChapter:
    return _own_chapter(db, user, chapter_id)


def _next_chapter_no(db: Session, book_id: int) -> int:
    current = db.scalar(
        select(func.max(BookChapter.chapter_no)).where(BookChapter.book_id == book_id)
    )
    return int(current or 0) + 1


def create_chapter(db: Session, user: SysUser, book_id: int, title: str, content: str) -> BookChapter:
    _own_book(db, user, book_id)

    chapter = BookChapter(
        book_id=book_id,
        chapter_no=_next_chapter_no(db, book_id),
        title=title.strip(),
        content=content.strip(),
        word_count=count_words(content),
        status=1,
        audit_status=CHAPTER_PENDING,
    )
    db.add(chapter)
    db.flush()

    book_service.recalc_stats(db, book_id)
    db.commit()
    db.refresh(chapter)
    return chapter


def update_chapter(db: Session, user: SysUser, chapter_id: int, payload) -> BookChapter:
    chapter = _own_chapter(db, user, chapter_id)

    if payload.title is not None:
        chapter.title = payload.title.strip()
    if payload.content is not None:
        chapter.content = payload.content.strip()
        chapter.word_count = count_words(payload.content)

    book_service.recalc_stats(db, chapter.book_id)
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_chapter(db: Session, user: SysUser, chapter_id: int) -> None:
    chapter = _own_chapter(db, user, chapter_id)

    # 逻辑删除：保留数据，前台不再展示
    chapter.status = 0
    book_service.recalc_stats(db, chapter.book_id)
    db.commit()


# ---------------------------------------------------------------
# 批量导入
# ---------------------------------------------------------------


def preview_chapters(db: Session, user: SysUser, book_id: int, raw_text: str) -> list[dict]:
    """按「第N章」切分，仅预览不落库。"""
    _own_book(db, user, book_id)

    parts = split_chapters(raw_text)
    items = []
    for index, (title, body) in enumerate(parts, start=1):
        items.append(
            {
                "index": index,
                "title": title,
                "word_count": count_words(body),
                "preview": body.strip().replace("\n", " ")[:60],
            }
        )
    return items


def import_chapters(db: Session, user: SysUser, book_id: int, raw_text: str) -> dict:
    _own_book(db, user, book_id)

    parts = split_chapters(raw_text)
    if not parts:
        raise BizError(1001, "没有解析到任何章节内容")
    if len(parts) > 500:
        raise BizError(1001, "一次最多导入 500 章")

    next_no = _next_chapter_no(db, book_id)
    total_words = 0

    for offset, (title, body) in enumerate(parts):
        words = count_words(body)
        total_words += words
        db.add(
            BookChapter(
                book_id=book_id,
                chapter_no=next_no + offset,
                title=title.strip()[:200] or f"第{next_no + offset}章",
                content=body.strip(),
                word_count=words,
                status=1,
                audit_status=CHAPTER_PENDING,
            )
        )

    db.flush()
    book_service.recalc_stats(db, book_id)
    db.commit()

    return {
        "imported": len(parts),
        "words": total_words,
        "first_chapter_no": next_no,
        "last_chapter_no": next_no + len(parts) - 1,
    }


# ---------------------------------------------------------------
# 作者主页与关注
# ---------------------------------------------------------------


def get_author(db: Session, author_id: int, viewer_id: int | None = None) -> dict:
    author = db.get(SysUser, author_id)
    if author is None or author.role not in ("author", "admin"):
        raise BizError(1004, "作者不存在")

    book_count = int(
        db.scalar(
            select(func.count())
            .select_from(Book)
            .where(Book.author_id == author_id, Book.is_online)
        )
        or 0
    )
    follower_count = int(
        db.scalar(
            select(func.count())
            .select_from(AuthorFollow)
            .where(AuthorFollow.author_id == author_id)
        )
        or 0
    )
    is_followed = False
    if viewer_id:
        is_followed = bool(
            db.scalar(
                select(AuthorFollow.id).where(
                    AuthorFollow.user_id == viewer_id, AuthorFollow.author_id == author_id
                )
            )
        )

    return {
        "id": author.id,
        "username": author.username,
        "nickname": author.nickname,
        "avatar": author.avatar,
        "bio": author.bio,
        "book_count": book_count,
        "follower_count": follower_count,
        "is_followed": is_followed,
    }


def follow(db: Session, user_id: int, author_id: int) -> dict:
    if user_id == author_id:
        raise BizError(1001, "不能关注自己")
    author = db.get(SysUser, author_id)
    if author is None or author.role not in ("author", "admin"):
        raise BizError(1004, "作者不存在")

    exists = db.scalar(
        select(AuthorFollow.id).where(
            AuthorFollow.user_id == user_id, AuthorFollow.author_id == author_id
        )
    )
    if exists:
        raise BizError(1001, "已经关注过了")

    db.add(AuthorFollow(user_id=user_id, author_id=author_id))
    db.commit()

    count = int(
        db.scalar(
            select(func.count())
            .select_from(AuthorFollow)
            .where(AuthorFollow.author_id == author_id)
        )
        or 0
    )
    return {"author_id": author_id, "is_followed": True, "follower_count": count}


def unfollow(db: Session, user_id: int, author_id: int) -> dict:
    row = db.scalar(
        select(AuthorFollow).where(
            AuthorFollow.user_id == user_id, AuthorFollow.author_id == author_id
        )
    )
    if row is None:
        raise BizError(1001, "还没有关注这位作者")

    db.delete(row)
    db.commit()

    count = int(
        db.scalar(
            select(func.count())
            .select_from(AuthorFollow)
            .where(AuthorFollow.author_id == author_id)
        )
        or 0
    )
    return {"author_id": author_id, "is_followed": False, "follower_count": count}


def my_follows(db: Session, user_id: int, page: int = 1, size: int = 12):
    total = int(
        db.scalar(
            select(func.count()).select_from(AuthorFollow).where(AuthorFollow.user_id == user_id)
        )
        or 0
    )
    rows = list(
        db.scalars(
            select(AuthorFollow)
            .where(AuthorFollow.user_id == user_id)
            .order_by(AuthorFollow.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    author_ids = [row.author_id for row in rows]
    authors = (
        {a.id: a for a in db.scalars(select(SysUser).where(SysUser.id.in_(author_ids))).all()}
        if author_ids
        else {}
    )

    items = []
    for row in rows:
        author = authors.get(row.author_id)
        if author is None:
            continue
        book_count = int(
            db.scalar(
                select(func.count())
                .select_from(Book)
                .where(Book.author_id == author.id, Book.is_online)
            )
            or 0
        )
        items.append(
            {
                "id": author.id,
                "username": author.username,
                "nickname": author.nickname,
                "avatar": author.avatar,
                "bio": author.bio,
                "book_count": book_count,
                "followed_at": row.created_at,
            }
        )
    return items, total
