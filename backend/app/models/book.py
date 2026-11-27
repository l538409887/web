"""书籍、分类、标签模型。"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import SysUser

book_tag_rel = Table(
    "book_tag_rel",
    Base.metadata,
    Column("book_id", BigInteger, ForeignKey("book.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("book_tag.id"), primary_key=True),
)


class BookCategory(Base):
    __tablename__ = "book_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    sort: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class BookTag(Base):
    __tablename__ = "book_tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("book_category.id"))
    cover: Mapped[str] = mapped_column(String(255), default="")
    intro: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(TINYINT, default=0)
    audit_status: Mapped[int] = mapped_column(TINYINT, default=1)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    chapter_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(BigInteger, default=0)
    collect_count: Mapped[int] = mapped_column(Integer, default=0)
    recommend_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=Decimal("0.0"))
    is_paid: Mapped[int] = mapped_column(TINYINT, default=0)
    @hybrid_property
    def is_online(self) -> bool:
        """前台可见 = 审核通过 且 已上架。"""
        return self.audit_status == 2 and self.shelf_status == 2

    @is_online.expression
    def is_online(cls):
        from sqlalchemy import and_

        return and_(cls.audit_status == 2, cls.shelf_status == 2)
    price_coin: Mapped[int] = mapped_column(Integer, default=0)
    revenue_coin: Mapped[int] = mapped_column(Integer, default=0)
    watermelon_count: Mapped[int] = mapped_column(Integer, default=0)
    paragraph_comment_count: Mapped[int] = mapped_column(Integer, default=0)
    last_chapter_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    last_chapter_title: Mapped[str] = mapped_column(String(200), default="")
    last_update_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    shelf_status: Mapped[int] = mapped_column(TINYINT, default=0)
    is_recommend: Mapped[int] = mapped_column(TINYINT, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    author: Mapped[SysUser] = relationship(SysUser, lazy="selectin")
    category: Mapped[BookCategory] = relationship(BookCategory, lazy="selectin")
    tags: Mapped[list[BookTag]] = relationship(
        BookTag, secondary=book_tag_rel, lazy="selectin"
    )
