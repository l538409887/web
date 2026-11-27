"""内容举报模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

TARGET_BOOK_COMMENT = "book_comment"
TARGET_PARAGRAPH_COMMENT = "paragraph_comment"


class ContentReport(Base):
    __tablename__ = "content_report"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[int] = mapped_column(BigInteger)
    reporter_id: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(200), default="")
    detail: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[int] = mapped_column(TINYINT, default=0)
    handled_by: Mapped[int | None] = mapped_column(BigInteger, default=None)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())