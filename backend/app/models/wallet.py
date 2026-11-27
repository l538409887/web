"""签到与充值订单模型。"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SignIn(Base):
    __tablename__ = "user_sign_in"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    sign_date: Mapped[date] = mapped_column(Date)
    reward: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RechargeOrder(Base):
    __tablename__ = "recharge_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(32))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    amount_fen: Mapped[int] = mapped_column(Integer)
    coin: Mapped[int] = mapped_column(Integer)
    status: Mapped[int] = mapped_column(TINYINT, default=0)
    remark: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    confirmed_by: Mapped[int | None] = mapped_column(BigInteger, default=None)