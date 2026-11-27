"""站点公告模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SiteNotice(Base):
    __tablename__ = "site_notice"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(String(500), default="")
    category: Mapped[str] = mapped_column(String(20), default="公告")
    is_top: Mapped[int] = mapped_column(TINYINT, default=0)
    status: Mapped[int] = mapped_column(TINYINT, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())