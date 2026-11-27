"""导入全部模型，保证 SQLAlchemy 注册表完整。"""
from app.models.base import Base
from app.models.book import Book, BookCategory, BookTag, book_tag_rel
from app.models.chapter import BookChapter
from app.models.comment import BookComment
from app.models.shelf import ReadingHistory, UserBookshelf
from app.models.user import SysUser
from app.models.interaction import (
    BookPurchase,
    ChapterPurchase,
    BookWatermelonLog,
    ParagraphComment,
    ParagraphReaction,
)
from app.models.follow import AuthorFollow
from app.models.notice import SiteNotice
from app.models.wallet import RechargeOrder, SignIn

__all__ = [
    "Base",
    "Book",
    "BookCategory",
    "BookTag",
    "book_tag_rel",
    "BookChapter",
    "BookComment",
    "ReadingHistory",
    "UserBookshelf",
    "SysUser",
]