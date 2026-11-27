"""书籍每日统计模型（周榜/月榜数据源）。"""
from datetime import date

from sqlalchemy import BigInteger, Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BookDailyStat(Base):
    __tablename__ = "book_daily_stat"
    __table_args__ = (UniqueConstraint("book_id", "stat_date", name="uk_book_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    book_id: Mapped[int] = mapped_column(BigInteger)
    stat_date: Mapped[date] = mapped_column(Date)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    collects: Mapped[int] = mapped_column(Integer, default=0)
    recommendations: Mapped[int] = mapped_column(Integer, default=0)