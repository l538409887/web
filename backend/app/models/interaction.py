"""购买、投喂西瓜、间贴模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BookPurchase(Base):
    __tablename__ = "book_purchase"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    coin: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ChapterPurchase(Base):
    __tablename__ = "chapter_purchase"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    chapter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book_chapter.id"))
    coin: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BookWatermelonLog(Base):
    __tablename__ = "book_watermelon_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ParagraphComment(Base):
    __tablename__ = "paragraph_comment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("paragraph_comment.id"), default=None
    )
    chapter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book_chapter.id"))
    paragraph_index: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    content: Mapped[str] = mapped_column(String(300))
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(TINYINT, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ParagraphReaction(Base):
    __tablename__ = "paragraph_reaction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("paragraph_comment.id")
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    reaction: Mapped[int] = mapped_column(TINYINT, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())