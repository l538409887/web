"""内容举报接口（读者端）。"""
from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["举报"])


class ReportIn(BaseModel):
    target_type: str = Field(description="book_comment 或 paragraph_comment")
    target_id: int
    reason: str = Field(max_length=200)
    detail: str = Field(default="", max_length=300)


@router.get("/reasons", summary="可选的举报理由")
def list_reasons():
    return ok(list(report_service.ALLOWED_REASONS))


@router.post("", summary="举报书评 / 间贴")
def create_report(
    payload: ReportIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = report_service.create_report(
        db, user.id, payload.target_type, payload.target_id, payload.reason, payload.detail
    )
    logger.bind(business=True).info(
        "REPORT_CREATE user={} type={} target={} reason={}",
        user.id,
        payload.target_type,
        payload.target_id,
        payload.reason,
    )
    return ok(result)