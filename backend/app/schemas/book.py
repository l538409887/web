"""书籍相关 Schema。"""
from pydantic import Field, field_validator

from app.schemas.common import APIModel, DateTimeStr


class AuthorBrief(APIModel):
    id: int
    username: str
    nickname: str


class CategoryBrief(APIModel):
    id: int
    name: str


class CategoryOut(CategoryBrief):
    book_count: int = 0


class BookCard(APIModel):
    id: int
    title: str
    cover: str
    author: AuthorBrief
    category: CategoryBrief
    status: int
    word_count: int
    chapter_count: int
    last_chapter_title: str
    last_update_at: DateTimeStr | None = None
    click_count: int = 0
    collect_count: int = 0
    recommend_count: int = 0
    is_paid: bool = False
    price_coin: int = 0
    revenue_coin: int = 0
    watermelon_count: int = 0
    paragraph_comment_count: int = 0
    intro: str = ""


class BookDetail(BookCard):
    last_chapter_id: int | None = None
    revenue_coin: int = 0
    is_purchased: bool = False
    intro: str
    tags: list[str] = Field(default_factory=list)
    score: float = 0.0
    is_recommend: bool = False
    created_at: DateTimeStr | None = None
    is_collected: bool = False

    @field_validator("tags", mode="before")
    @classmethod
    def _flatten_tags(cls, value):
        if not value:
            return []
        return [getattr(item, "name", str(item)) for item in value]