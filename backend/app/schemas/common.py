"""通用 Schema：时间格式、分页结构。"""
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, PlainSerializer

T = TypeVar("T")


def _fmt_dt(value: datetime | None):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


DateTimeStr = Annotated[datetime, PlainSerializer(_fmt_dt, return_type=str)]


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageResult(BaseModel, Generic[T]):
    list: list[T]
    total: int
    page: int
    size: int
    pages: int