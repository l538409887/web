"""作者中心 Schema。"""
from pydantic import BaseModel, Field

from app.schemas.common import APIModel, DateTimeStr


class AuthorBookIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    category_id: int
    intro: str = Field(min_length=1, max_length=2000)
    cover: str = ""
    status: int = 0


class AuthorBookUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: int | None = None
    intro: str | None = Field(default=None, min_length=1, max_length=2000)
    cover: str | None = None
    status: int | None = None


class ChapterIn(BaseModel):
    # 标题留空时由服务端按章节序号生成「第N章」
    title: str = Field(default="", max_length=200)
    content: str = Field(default="")
    # True 表示暂存草稿：不做敏感词校验，不进审核队列
    draft: bool = False


class ChapterUpdateIn(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    # draft 存为草稿 / submit 提交审核 / None 保持不变
    action: str | None = None


class ChapterItem(APIModel):
    id: int
    book_id: int
    chapter_no: int
    title: str
    word_count: int = 0
    status: int = 1
    audit_status: int = 1
    created_at: DateTimeStr | None = None