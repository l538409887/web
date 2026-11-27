"""书架与阅读进度模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.book import Book


class UserBookshelf(Base):
    __tablename__ = "user_bookshelf"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    is_top: Mapped[int] = mapped_column(TINYINT, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    book: Mapped[Book] = relationship(Book, lazy="selectin")


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    chapter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book_chapter.id"))
    chapter_no: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[int] = mapped_column(TINYINT, default=0)
    read_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )