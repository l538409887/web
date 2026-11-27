"""敏感词模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SensitiveWord(Base):
    __tablename__ = "sensitive_word"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word: Mapped[str] = mapped_column(String(50))
    level: Mapped[str] = mapped_column(String(10), default="review")
    category: Mapped[str] = mapped_column(String(20), default="其他")
    is_active: Mapped[int] = mapped_column(TINYINT, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())