"""章节相关 Schema。"""
from app.schemas.common import APIModel, DateTimeStr


class ChapterBrief(APIModel):
    id: int
    chapter_no: int
    title: str
    word_count: int = 0
    created_at: DateTimeStr | None = None
    locked: bool = False
    price_coin: int = 0
    chapter_price: int = 0
    is_paid: bool = False


class ChapterDetail(APIModel):
    id: int
    book_id: int
    book_title: str = ""
    chapter_no: int
    title: str
    content: str = ""
    word_count: int = 0
    prev_id: int | None = None
    next_id: int | None = None
    is_collected: bool = False
    locked: bool = False
    price_coin: int = 0
    chapter_price: int = 0
    is_paid: bool = False