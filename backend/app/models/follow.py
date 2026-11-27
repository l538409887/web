"""作者关注模型。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuthorFollow(Base):
    __tablename__ = "author_follow"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())