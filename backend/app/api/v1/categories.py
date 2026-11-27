"""分类接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.services import book_service

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", summary="分类列表（含书籍数量）")
def list_categories(db: Session = Depends(get_db)):
    return ok(book_service.list_categories(db))