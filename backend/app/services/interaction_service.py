"""付费购买、投喂西瓜、间贴（段落评论）业务。"""
import math
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.book import Book
from app.models.chapter import BookChapter
from app.models.interaction import (
    BookPurchase,
    BookWatermelonLog,
    ChapterPurchase,
    ParagraphComment,
    ParagraphReaction,
)
from app.models.user import SysUser

COIN_PER_KILO_WORD = 5
MIN_PAID_WORDS = 100000
FREE_PREVIEW_CHAPTERS = 3
MAX_FEED_PER_TIME = 99
# 同一本书每天最多投喂 2 个西瓜，防止刷榜
DAILY_FEED_LIMIT_PER_BOOK = 2


# 计价说明：每千字 5 软妹币（即 0.05 元）。按字数比例计算后向上取整到整数软妹币，
# 不能先对"千字数"取整再乘，否则 1042 字会被当成 2 千字，价格翻倍。
def calc_price(word_count: int) -> int:
    """整本价格（软妹币）。"""
    words = max(0, word_count)
    if words == 0:
        return 0
    return max(1, math.ceil(words * COIN_PER_KILO_WORD / 1000))


def calc_chapter_price(word_count: int) -> int:
    """单章价格（软妹币），至少 1 个。"""
    return max(1, math.ceil(max(0, word_count) * COIN_PER_KILO_WORD / 1000))


def is_chapter_purchased(db: Session, user_id: int, chapter_id: int) -> bool:
    return bool(
        db.scalar(
            select(ChapterPurchase.id).where(
                ChapterPurchase.user_id == user_id,
                ChapterPurchase.chapter_id == chapter_id,
            )
        )
    )


def purchased_chapter_ids(db: Session, user_id: int, book_id: int) -> set[int]:
    return set(
        db.scalars(
            select(ChapterPurchase.chapter_id).where(
                ChapterPurchase.user_id == user_id, ChapterPurchase.book_id == book_id
            )
        ).all()
    )


def paid_amount_for_book(db: Session, user_id: int, book_id: int) -> int:
    """该用户在这本书上已花掉的单章费用合计。"""
    return int(
        db.scalar(
            select(func.coalesce(func.sum(ChapterPurchase.coin), 0)).where(
                ChapterPurchase.user_id == user_id, ChapterPurchase.book_id == book_id
            )
        )
        or 0
    )


def is_purchased(db: Session, user_id: int, book_id: int) -> bool:
    return bool(
        db.scalar(
            select(BookPurchase.id).where(
                BookPurchase.user_id == user_id, BookPurchase.book_id == book_id
            )
        )
    )


def set_paid(db: Session, user: SysUser, book_id: int, is_paid: bool) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise BizError(3001, "书籍不存在")
    if book.author_id != user.id and user.role != "admin":
        raise BizError(6001, "只能管理自己的作品")

    if is_paid:
        if book.word_count < MIN_PAID_WORDS:
            raise BizError(
                1001, f"作品字数需达到 {MIN_PAID_WORDS // 10000} 万字才能开启付费"
            )
        book.is_paid = 1
        book.price_coin = calc_price(book.word_count)
    else:
        book.is_paid = 0
        book.price_coin = 0

    db.commit()
    db.refresh(book)
    return book


def buy_book(db: Session, user_id: int, book_id: int) -> dict:
    book = db.get(Book, book_id)
    if book is None or book.audit_status != 1:
        raise BizError(3001, "书籍不存在或已下架")
    if book.is_paid != 1:
        raise BizError(1001, "这本书是免费的，无需购买")
    if is_purchased(db, user_id, book_id):
        raise BizError(1001, "你已购买过这本书")

    full_price = book.price_coin or calc_price(book.word_count)
    already_paid = paid_amount_for_book(db, user_id, book_id)
    price = max(0, full_price - already_paid)

    user = db.get(SysUser, user_id)
    if user is None:
        raise BizError(1004, "用户不存在")
    if user.coin < price:
        raise BizError(1001, f"软妹币不足，还需要 {price - user.coin}")

    try:
        db.add(BookPurchase(user_id=user_id, book_id=book_id, coin=price))
        db.execute(
            update(SysUser).where(SysUser.id == user_id).values(coin=SysUser.coin - price)
        )
        db.execute(
            update(Book)
            .where(Book.id == book_id)
            .values(revenue_coin=Book.revenue_coin + price)
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError(1001, "你已购买过这本书")

    # 提交后重新查库，避免会话内对象被 update() 同步导致重复扣减
    balance = db.scalar(select(SysUser.coin).where(SysUser.id == user_id)) or 0
    return {"book_id": book_id, "coin": price, "balance": int(balance)}


def can_read_chapter(db: Session, user_id: int | None, book: Book, chapter: BookChapter) -> bool:
    if book.is_paid != 1:
        return True
    if chapter.chapter_no <= FREE_PREVIEW_CHAPTERS:
        return True
    if user_id is None:
        return False
    if is_purchased(db, user_id, book.id):
        return True
    return is_chapter_purchased(db, user_id, chapter.id)


def feed_watermelon(db: Session, user_id: int, book_id: int, count: int) -> dict:
    if count < 1 or count > MAX_FEED_PER_TIME:
        raise BizError(1001, f"每次可投喂 1~{MAX_FEED_PER_TIME} 个西瓜")

    book = db.scalar(select(Book).where(Book.id == book_id, Book.audit_status == 1))
    if book is None:
        raise BizError(3001, "书籍不存在或已下架")

    user = db.get(SysUser, user_id)
    if user is None:
        raise BizError(1004, "用户不存在")
    if user.watermelon < count:
        raise BizError(1001, f"西瓜不足，当前只有 {user.watermelon} 个")

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    used_today = int(
        db.scalar(
            select(func.coalesce(func.sum(BookWatermelonLog.count), 0)).where(
                BookWatermelonLog.user_id == user_id,
                BookWatermelonLog.book_id == book_id,
                BookWatermelonLog.created_at >= today_start,
            )
        )
        or 0
    )
    remain = max(0, DAILY_FEED_LIMIT_PER_BOOK - used_today)
    if count > remain:
        if remain == 0:
            raise BizError(
                1001, f"每本书每天最多投喂 {DAILY_FEED_LIMIT_PER_BOOK} 个西瓜，今天已经喂满了"
            )
        raise BizError(
            1001, f"每本书每天最多投喂 {DAILY_FEED_LIMIT_PER_BOOK} 个西瓜，今天还能喂 {remain} 个"
        )

    db.execute(
        update(SysUser).where(SysUser.id == user_id).values(watermelon=SysUser.watermelon - count)
    )
    db.execute(
        update(Book).where(Book.id == book_id).values(watermelon_count=Book.watermelon_count + count)
    )
    db.add(BookWatermelonLog(user_id=user_id, book_id=book_id, count=count))
    db.commit()

    # 提交后重新查库，取真实余额与总数
    left = db.scalar(select(SysUser.watermelon).where(SysUser.id == user_id)) or 0
    total = db.scalar(select(Book.watermelon_count).where(Book.id == book_id)) or 0
    return {
        "book_id": book_id,
        "fed": count,
        "watermelon_left": int(left),
        "book_watermelon": int(total),
        "fed_today": used_today + count,
        "daily_limit": DAILY_FEED_LIMIT_PER_BOOK,
        "remain_today": max(0, remain - count),
    }


# ---------------- 间贴 ----------------
def _user_brief(user: SysUser | None) -> dict:
    return {
        "id": user.id if user else 0,
        "username": user.username if user else "",
        "nickname": user.nickname if user else "",
        "avatar": user.avatar if user else "",
    }


def _comment_item(row: ParagraphComment, users: dict) -> dict:
    return {
        "id": row.id,
        "parent_id": row.parent_id,
        "paragraph_index": row.paragraph_index,
        "content": row.content,
        "like_count": row.like_count,
        "dislike_count": row.dislike_count,
        "report_count": row.report_count,
        "reply_count": row.reply_count,
        "created_at": row.created_at,
        "user": _user_brief(users.get(row.user_id)),
    }


def list_paragraph_comments(db: Session, chapter_id: int) -> dict:
    rows = list(
        db.scalars(
            select(ParagraphComment).where(
                ParagraphComment.chapter_id == chapter_id, ParagraphComment.status == 1
            )
        ).all()
    )

    user_ids = {row.user_id for row in rows}
    users = (
        {u.id: u for u in db.scalars(select(SysUser).where(SysUser.id.in_(user_ids))).all()}
        if user_ids
        else {}
    )

    replies: dict[int, list[ParagraphComment]] = {}
    tops: list[ParagraphComment] = []
    for row in rows:
        if row.parent_id is None:
            tops.append(row)
        else:
            replies.setdefault(row.parent_id, []).append(row)

    tops.sort(key=lambda r: (r.like_count, r.id), reverse=True)

    grouped: dict[int, list[dict]] = {}
    for row in tops:
        item = _comment_item(row, users)
        kids = sorted(replies.get(row.id, []), key=lambda r: r.id)
        item["replies"] = [_comment_item(k, users) for k in kids]
        item["reply_count"] = len(kids)
        grouped.setdefault(row.paragraph_index, []).append(item)

    return {"total": len(rows), "grouped": grouped}


def add_paragraph_comment(
    db: Session,
    user: SysUser,
    book_id: int,
    chapter_id: int,
    paragraph_index: int,
    content: str,
    parent_id: int | None = None,
) -> ParagraphComment:
    text = content.strip()
    if not text:
        raise BizError(5001, "评论内容不能为空")
    if len(text) > 300:
        raise BizError(5001, "间贴最多 300 字")

    parent = None
    if parent_id:
        parent = db.get(ParagraphComment, parent_id)
        if parent is None or parent.status != 1:
            raise BizError(1004, "要回复的间贴不存在")
        if parent.parent_id is not None:
            raise BizError(1001, "只能回复顶层间贴，不支持多级嵌套")
        # 回复一律挂在父间贴所在的段落上，忽略前端传的坐标
        book_id = parent.book_id
        chapter_id = parent.chapter_id
        paragraph_index = parent.paragraph_index

    chapter = db.get(BookChapter, chapter_id)
    if chapter is None or chapter.book_id != book_id:
        raise BizError(3002, "章节不存在")
    if paragraph_index < 0 or paragraph_index > 2000:
        raise BizError(1001, "段落序号不合法")

    comment = ParagraphComment(
        book_id=book_id,
        parent_id=parent.id if parent else None,
        chapter_id=chapter_id,
        paragraph_index=paragraph_index,
        user_id=user.id,
        content=text,
        status=1,
    )
    db.add(comment)

    if parent is not None:
        db.execute(
            update(ParagraphComment)
            .where(ParagraphComment.id == parent.id)
            .values(reply_count=ParagraphComment.reply_count + 1)
        )
    else:
        # 只有顶层间贴计入书籍的间贴总数（吐槽榜依据）
        db.execute(
            update(Book)
            .where(Book.id == book_id)
            .values(paragraph_comment_count=Book.paragraph_comment_count + 1)
        )

    db.commit()
    db.refresh(comment)
    return comment


def my_paragraph_comments(db: Session, user_id: int, page: int = 1, size: int = 10):
    base = ParagraphComment.user_id == user_id
    total = int(db.scalar(select(func.count()).select_from(ParagraphComment).where(base)) or 0)

    rows = list(
        db.scalars(
            select(ParagraphComment)
            .where(base)
            .order_by(ParagraphComment.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    book_ids = {r.book_id for r in rows}
    books = (
        {b.id: b.title for b in db.scalars(select(Book).where(Book.id.in_(book_ids))).all()}
        if book_ids
        else {}
    )
    chapter_ids = {r.chapter_id for r in rows}
    chapters = (
        {
            c.id: c.title
            for c in db.scalars(select(BookChapter).where(BookChapter.id.in_(chapter_ids))).all()
        }
        if chapter_ids
        else {}
    )

    parent_ids = {r.parent_id for r in rows if r.parent_id}
    parents = (
        {
            p.id: p.content
            for p in db.scalars(
                select(ParagraphComment).where(ParagraphComment.id.in_(parent_ids))
            ).all()
        }
        if parent_ids
        else {}
    )

    items = []
    for row in rows:
        items.append(
            {
                "id": row.id,
                "parent_id": row.parent_id,
                "parent_content": parents.get(row.parent_id, "") if row.parent_id else "",
                "book_id": row.book_id,
                "book_title": books.get(row.book_id, ""),
                "chapter_id": row.chapter_id,
                "chapter_title": chapters.get(row.chapter_id, ""),
                "paragraph_index": row.paragraph_index,
                "content": row.content,
                "like_count": row.like_count,
                "dislike_count": row.dislike_count,
                "reply_count": row.reply_count,
                "status": row.status,
                "created_at": row.created_at,
            }
        )
    return items, total


def react_paragraph_comment(
    db: Session, user: SysUser, comment_id: int, reaction: int
) -> dict:
    if reaction not in (1, 2, 3):
        raise BizError(1001, "reaction 只能是 1赞 / 2踩 / 3举报")

    comment = db.get(ParagraphComment, comment_id)
    if comment is None or comment.status != 1:
        raise BizError(1004, "间贴不存在")

    existing = db.scalar(
        select(ParagraphReaction).where(
            ParagraphReaction.comment_id == comment_id,
            ParagraphReaction.user_id == user.id,
        )
    )

    def bump(field: str, delta: int) -> None:
        column = getattr(ParagraphComment, field)
        db.execute(
            update(ParagraphComment).where(ParagraphComment.id == comment_id).values(
                {field: column + delta}
            )
        )

    if existing is None:
        db.add(ParagraphReaction(comment_id=comment_id, user_id=user.id, reaction=reaction))
        bump({1: "like_count", 2: "dislike_count", 3: "report_count"}[reaction], 1)
        db.commit()
        return {"reaction": reaction, "state": "on"}

    if existing.reaction == reaction:
        db.delete(existing)
        bump({1: "like_count", 2: "dislike_count", 3: "report_count"}[reaction], -1)
        db.commit()
        return {"reaction": 0, "state": "off"}

    bump({1: "like_count", 2: "dislike_count", 3: "report_count"}[existing.reaction], -1)
    bump({1: "like_count", 2: "dislike_count", 3: "report_count"}[reaction], 1)
    existing.reaction = reaction
    db.commit()
    return {"reaction": reaction, "state": "on"}


def hide_paragraph_comment(db: Session, user: SysUser, comment_id: int) -> None:
    comment = db.get(ParagraphComment, comment_id)
    if comment is None or comment.status == 0:
        raise BizError(1004, "间贴不存在")
    if comment.user_id != user.id and user.role != "admin":
        raise BizError(5002, "只能删除自己的间贴")

    comment.status = 0
    if comment.parent_id is None:
        # 顶层间贴被删，其回复一并隐藏
        db.execute(
            update(ParagraphComment)
            .where(
                ParagraphComment.parent_id == comment.id,
                ParagraphComment.status == 1,
            )
            .values(status=0)
        )
        db.execute(
            update(Book)
            .where(Book.id == comment.book_id, Book.paragraph_comment_count > 0)
            .values(paragraph_comment_count=Book.paragraph_comment_count - 1)
        )
    db.commit()


# ---------------- 更新榜 ----------------
def monthly_update_rank(db: Session, limit: int = 10) -> list[dict]:
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = db.execute(
        select(
            BookChapter.book_id,
            func.sum(BookChapter.word_count).label("words"),
            func.count(BookChapter.id).label("chapters"),
        )
        .where(BookChapter.created_at >= month_start, BookChapter.status == 1)
        .group_by(BookChapter.book_id)
        .order_by(func.sum(BookChapter.word_count).desc())
        .limit(limit)
    ).all()

    if not rows:
        return []

    book_ids = [row.book_id for row in rows]
    books = {
        b.id: b
        for b in db.scalars(
            select(Book).where(Book.id.in_(book_ids), Book.audit_status == 1)
        ).all()
    }

    result = []
    for index, row in enumerate(rows, start=1):
        book = books.get(row.book_id)
        if book is None:
            continue
        result.append(
            {
                "rank": len(result) + 1,
                "book": book,
                "words": int(row.words or 0),
                "chapters": int(row.chapters or 0),
            }
        )
    return result

# ---------------- 后台审核 ----------------
def admin_list_paragraph_comments(
    db: Session,
    *,
    status: int | None = None,
    only_reported: bool = False,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    conditions = []
    if status is not None:
        conditions.append(ParagraphComment.status == status)
    if only_reported:
        conditions.append(ParagraphComment.report_count > 0)

    total = int(
        db.scalar(select(func.count()).select_from(ParagraphComment).where(*conditions)) or 0
    )
    rows = list(
        db.scalars(
            select(ParagraphComment)
            .where(*conditions)
            .order_by(ParagraphComment.report_count.desc(), ParagraphComment.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    book_ids = {row.book_id for row in rows}
    books = (
        {b.id: b.title for b in db.scalars(select(Book).where(Book.id.in_(book_ids))).all()}
        if book_ids
        else {}
    )
    chapter_ids = {row.chapter_id for row in rows}
    chapters = (
        {c.id: c.title for c in db.scalars(select(BookChapter).where(BookChapter.id.in_(chapter_ids))).all()}
        if chapter_ids
        else {}
    )
    user_ids = {row.user_id for row in rows}
    users = (
        {u.id: u for u in db.scalars(select(SysUser).where(SysUser.id.in_(user_ids))).all()}
        if user_ids
        else {}
    )

    items = []
    for row in rows:
        user = users.get(row.user_id)
        items.append(
            {
                "id": row.id,
                "book_id": row.book_id,
                "book_title": books.get(row.book_id, ""),
                "chapter_id": row.chapter_id,
                "chapter_title": chapters.get(row.chapter_id, ""),
                "paragraph_index": row.paragraph_index,
                "content": row.content,
                "like_count": row.like_count,
                "dislike_count": row.dislike_count,
                "report_count": row.report_count,
                "status": row.status,
                "created_at": row.created_at,
                "username": user.username if user else "",
                "nickname": user.nickname if user else "",
            }
        )
    return items, total


def set_paragraph_status(db: Session, comment_id: int, status: int) -> None:
    if status not in (0, 1):
        raise BizError(1001, "status 只能是 0 隐藏 / 1 恢复")

    comment = db.get(ParagraphComment, comment_id)
    if comment is None:
        raise BizError(1004, "间贴不存在")
    if comment.status == status:
        return

    comment.status = status
    if comment.parent_id is None:
        if status == 0:
            db.execute(
                update(ParagraphComment)
                .where(
                    ParagraphComment.parent_id == comment.id,
                    ParagraphComment.status == 1,
                )
                .values(status=0)
            )
            db.execute(
                update(Book)
                .where(Book.id == comment.book_id, Book.paragraph_comment_count > 0)
                .values(paragraph_comment_count=Book.paragraph_comment_count - 1)
            )
        else:
            db.execute(
                update(Book)
                .where(Book.id == comment.book_id)
                .values(paragraph_comment_count=Book.paragraph_comment_count + 1)
            )
    db.commit()


def chapter_locks(
    db: Session, user_id: int | None, book_id: int, chapters: list[BookChapter]
) -> dict[int, dict]:
    """批量计算章节锁定状态与单章价格（用于章节目录）。"""
    book = db.get(Book, book_id)
    if book is None or book.is_paid != 1:
        return {}

    owns = bool(user_id) and is_purchased(db, user_id, book_id)
    owned = (
        purchased_chapter_ids(db, user_id, book_id)
        if (user_id and not owns)
        else set()
    )

    result: dict[int, dict] = {}
    for chapter in chapters:
        locked = (
            not owns
            and chapter.chapter_no > FREE_PREVIEW_CHAPTERS
            and chapter.id not in owned
        )
        result[chapter.id] = {
            "locked": locked,
            "price_coin": calc_chapter_price(chapter.word_count),
        }
    return result


def buy_chapters(
    db: Session, user_id: int, book_id: int, chapter_ids: list[int]
) -> dict:
    book = db.get(Book, book_id)
    if book is None or book.audit_status != 1:
        raise BizError(3001, "书籍不存在或已下架")
    if book.is_paid != 1:
        raise BizError(1001, "这本书是免费的，无需购买")
    if is_purchased(db, user_id, book_id):
        raise BizError(1001, "你已购买整本，无需再买单章")

    ids = list(dict.fromkeys(chapter_ids))
    if not ids:
        raise BizError(1001, "请选择要购买的章节")
    if len(ids) > 200:
        raise BizError(1001, "一次最多购买 200 章")

    rows = list(
        db.scalars(
            select(BookChapter).where(
                BookChapter.id.in_(ids), BookChapter.book_id == book_id
            )
        ).all()
    )
    if len(rows) != len(ids):
        raise BizError(3002, "部分章节不存在")

    free = [c for c in rows if c.chapter_no <= FREE_PREVIEW_CHAPTERS]
    if free:
        raise BizError(1001, f"前 {FREE_PREVIEW_CHAPTERS} 章免费，无需购买")

    owned = purchased_chapter_ids(db, user_id, book_id)
    dup = [c for c in rows if c.id in owned]
    if dup:
        raise BizError(1001, "部分章节已购买，请刷新后重试")

    total = sum(calc_chapter_price(c.word_count) for c in rows)

    user = db.get(SysUser, user_id)
    if user is None:
        raise BizError(1004, "用户不存在")
    if user.coin < total:
        raise BizError(1001, f"软妹币不足，还需要 {total - user.coin}")

    try:
        db.add_all(
            [
                ChapterPurchase(
                    user_id=user_id,
                    book_id=book_id,
                    chapter_id=c.id,
                    coin=calc_chapter_price(c.word_count),
                )
                for c in rows
            ]
        )
        db.execute(
            update(SysUser).where(SysUser.id == user_id).values(coin=SysUser.coin - total)
        )
        db.execute(
            update(Book).where(Book.id == book_id).values(revenue_coin=Book.revenue_coin + total)
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError(1001, "部分章节已购买，请刷新后重试")

    balance = db.scalar(select(SysUser.coin).where(SysUser.id == user_id)) or 0
    return {
        "book_id": book_id,
        "count": len(rows),
        "coin": total,
        "balance": int(balance),
    }