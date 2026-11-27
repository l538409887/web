"""书架与阅读进度 Schema。"""
from app.schemas.book import BookCard
from app.schemas.chapter import ChapterBrief
from app.schemas.common import APIModel, DateTimeStr


class LastReadOut(APIModel):
    chapter_id: int
    chapter_no: int
    chapter_title: str = ""
    progress: int = 0
    updated_at: DateTimeStr | None = None


class ShelfItem(APIModel):
    book: BookCard
    is_top: bool = False
    last_read: LastReadOut | None = None
    has_update: bool = False


class HistoryItem(APIModel):
    book: BookCard
    chapter: ChapterBrief
    progress: int = 0
    updated_at: DateTimeStr | None = None