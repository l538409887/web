"""评论模型（书评 + 章评 + 一层回复）。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import SysUser


class BookComment(Base):
    __tablename__ = "book_comment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book.id"))
    chapter_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("book_chapter.id"), default=None
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    parent_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    content: Mapped[str] = mapped_column(String(500))
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(TINYINT, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[SysUser] = relationship(SysUser, lazy="selectin")