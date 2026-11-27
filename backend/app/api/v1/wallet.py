"""钱包接口：签到、充值订单。"""
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.common import PageResult
from app.schemas.wallet import OrderOut, RechargeIn, WalletOut
from app.services import wallet_service

router = APIRouter(prefix="/wallet", tags=["钱包"])


@router.get("", summary="钱包信息（余额 / 西瓜 / 今日是否签到）")
def get_wallet(user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(WalletOut(**wallet_service.get_wallet(db, user.id)))


@router.post("/sign-in", summary="每日签到")
def sign_in(user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    data = wallet_service.sign_in(db, user.id)
    logger.bind(business=True).info(
        "SIGN_IN user={} reward={} total_days={}",
        user.id,
        data["sign_reward"],
        data["total_sign_days"],
    )
    return ok(WalletOut(**data))


@router.get("/pay-info", summary="充值信息（收款码 / 档位）")
def pay_info():
    return ok(wallet_service.pay_info())


@router.get("/orders", summary="我的充值订单")
def my_orders(
    page: int = 1,
    size: int = 10,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = wallet_service.list_my_orders(db, user.id, page, size)
    items = [OrderOut.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[OrderOut](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.post("/orders", summary="创建充值订单")
def create_order(
    payload: RechargeIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = wallet_service.create_order(db, user.id, payload.amount_fen)
    logger.bind(business=True).info(
        "ORDER_CREATE user={} order={} fen={}", user.id, order.order_no, order.amount_fen
    )
    return ok(OrderOut.model_validate(order))