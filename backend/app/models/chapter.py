"""章节模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BookChapter(Base):
    __tablename__ = "book_chapter"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(BigInteger)
    chapter_no: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(TINYINT, default=1)
    audit_status: Mapped[int] = mapped_column(TINYINT, default=1)
    @hybrid_property
    def is_visible(self) -> bool:
        """阅读端可见 = 未隐藏 且 审核通过。"""
        return self.status == 1 and self.audit_status == 2

    @is_visible.expression
    def is_visible(cls):
        from sqlalchemy import and_

        return and_(cls.status == 1, cls.audit_status == 2)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
