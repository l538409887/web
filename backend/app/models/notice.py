"""站内通知与站点公告模型。"""
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


class UserNotice(Base):
    """站内通知：审核结果、上架结果、举报处理等，发给具体用户。"""

    __tablename__ = "user_notice"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(20), default="system")
    title: Mapped[str] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(String(500), default="")
    link: Mapped[str] = mapped_column(String(200), default="")
    is_read: Mapped[int] = mapped_column(TINYINT, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())