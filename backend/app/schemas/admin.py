"""管理后台 Schema。"""
from pydantic import BaseModel, Field

from app.schemas.auth import UserBriefOut
from app.schemas.book import BookCard
from app.schemas.common import APIModel, DateTimeStr


class StatsOut(BaseModel):
    user_count: int
    book_count: int
    chapter_count: int
    comment_count: int
    category_count: int
    today_new_users: int = 0
    today_new_books: int = 0
    today_new_chapters: int = 0
    today_new_comments: int = 0


class AdminBookItem(BookCard):
    audit_status: int = 1
    shelf_status: int = 0
    is_recommend: bool = False
    created_at: DateTimeStr | None = None
    intro: str = ""


class BookStatusIn(BaseModel):
    audit_status: int | None = None
    shelf_status: int | None = None
    is_recommend: bool | None = None


class BookCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author_id: int
    category_id: int
    intro: str = Field(min_length=1, max_length=2000)
    cover: str = ""
    status: int = 0
    is_recommend: bool = False


class ChapterImportIn(BaseModel):
    raw_text: str = Field(min_length=1)


class AdminUserItem(UserBriefOut):
    email: str | None = None
    bio: str = ""
    status: int = 1
    created_at: DateTimeStr | None = None
    last_login_at: DateTimeStr | None = None


class UserUpdateIn(BaseModel):
    status: int | None = None
    role: str | None = None


class AdminCommentItem(APIModel):
    id: int
    book_id: int
    book_title: str = ""
    chapter_id: int | None = None
    chapter_title: str = ""
    user: UserBriefOut
    content: str
    status: int = 1
    created_at: DateTimeStr | None = None


class CommentStatusIn(BaseModel):
    status: int = Field(ge=0, le=2)


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    sort: int = 0