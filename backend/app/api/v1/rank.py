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


@router.get("/period", summary="周榜 / 月榜（按日流水聚合）")
def period_rank(
    metric: str = "click",
    period: str = "week",
    limit: int = 20,
    db: Session = Depends(get_db),
):
    from app.services import stat_service

    limit = min(max(1, limit), 50)
    rows = stat_service.period_top(db, metric=metric, period=period, limit=limit)
    return ok(
        {
            "period": period,
            "metric": metric,
            "list": [
                {
                    "rank": index,
                    "value": item["value"],
                    "book": BookCard.model_validate(item["book"]),
                }
                for index, item in enumerate(rows, start=1)
            ],
        }
    )