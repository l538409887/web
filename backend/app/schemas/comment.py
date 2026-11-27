"""评论相关 Schema（含一层回复）。"""
from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import UserBriefOut
from app.schemas.common import APIModel, DateTimeStr


class CommentCreateIn(BaseModel):
    book_id: int
    chapter_id: int | None = None
    parent_id: int | None = None
    content: str = Field(min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def _strip_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("评论内容不能为空")
        return text


class CommentOut(APIModel):
    id: int
    user: UserBriefOut
    content: str
    like_count: int = 0
    created_at: DateTimeStr | None = None
    parent_id: int | None = None
    replies: list["CommentOut"] = Field(default_factory=list)


CommentOut.model_rebuild()

class MyCommentItem(APIModel):
    id: int
    book_id: int
    book_title: str = ""
    chapter_id: int | None = None
    chapter_title: str = ""
    content: str
    like_count: int = 0
    status: int = 1
    created_at: DateTimeStr | None = None