"""榜单接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ok
from app.schemas.book import BookCard
from app.services import interaction_service

router = APIRouter(prefix="/rank", tags=["榜单"])


@router.get("/monthly", summary="更新榜（本月更新字数）")
def monthly_rank(limit: int = 10, db: Session = Depends(get_db)):
    limit = min(max(1, limit), 50)
    rows = interaction_service.monthly_update_rank(db, limit)
    return ok(
        [
            {
                "rank": item["rank"],
                "words": item["words"],
                "chapters": item["chapters"],
                "book": BookCard.model_validate(item["book"]),
            }
            for item in rows
        ]
    )