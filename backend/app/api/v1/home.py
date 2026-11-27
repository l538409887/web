"""首页聚合接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.schemas.book import BookCard, BookDetail
from app.services import home_service

router = APIRouter(prefix="/home", tags=["首页"])


@router.get("", summary="首页聚合数据")
def home(db: Session = Depends(get_db)):
    data = home_service.get_home(db)
    return ok(
        {
            "banners": [BookDetail.model_validate(b) for b in data["banners"]],
            "categories": data["categories"],
            "ranks": {
                key: [BookCard.model_validate(b) for b in books]
                for key, books in data["ranks"].items()
            },
            "latest": [BookCard.model_validate(b) for b in data["latest"]],
            "sections": {
                key: [BookDetail.model_validate(b) for b in books]
                for key, books in data["sections"].items()
            },
        }
    )
