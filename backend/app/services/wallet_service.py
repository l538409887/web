"""签到与充值业务。

设计说明：
- 签到防重复：依赖 `uk_user_date(user_id, sign_date)` 唯一索引，
  并发下由数据库兜底，捕获 IntegrityError 后返回业务错误。
- 充值到账：订单从「待支付」变「已到账」时，在同一事务内同时改订单状态和加余额，
  订单状态用条件更新（WHERE status = 0）保证不会重复到账。
"""
import random
import string
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizError
from app.models.user import SysUser
from app.models.wallet import RechargeOrder, SignIn

SIGN_REWARD = 1
COIN_PER_YUAN = 100
ALLOWED_AMOUNTS_FEN = [100, 500, 1000, 2000, 5000, 10000]


def _user(db: Session, user_id: int) -> SysUser:
    user = db.get(SysUser, user_id)
    if user is None:
        raise BizError(1004, "用户不存在")
    return user


def get_wallet(db: Session, user_id: int) -> dict:
    user = _user(db, user_id)
    today = date.today()

    signed = db.scalar(
        select(SignIn.id).where(SignIn.user_id == user_id, SignIn.sign_date == today)
    )
    total_days = int(
        db.scalar(
            select(func.count()).select_from(SignIn).where(SignIn.user_id == user_id)
        )
        or 0
    )

    return {
        "coin": user.coin,
        "watermelon": user.watermelon,
        "signed_today": bool(signed),
        "total_sign_days": total_days,
        "sign_reward": SIGN_REWARD,
        "coin_per_yuan": COIN_PER_YUAN,
    }


def sign_in(db: Session, user_id: int) -> dict:
    today = date.today()

    exists = db.scalar(
        select(SignIn.id).where(SignIn.user_id == user_id, SignIn.sign_date == today)
    )
    if exists:
        raise BizError(1001, "今天已经签到过了，明天再来")

    try:
        db.add(SignIn(user_id=user_id, sign_date=today, reward=SIGN_REWARD))
        db.execute(
            update(SysUser)
            .where(SysUser.id == user_id)
            .values(watermelon=SysUser.watermelon + SIGN_REWARD)
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BizError(1001, "今天已经签到过了，明天再来")

    return get_wallet(db, user_id)


def _gen_order_no() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + "".join(
        random.choices(string.digits, k=4)
    )


def create_order(db: Session, user_id: int, amount_fen: int) -> RechargeOrder:
    if amount_fen not in ALLOWED_AMOUNTS_FEN:
        raise BizError(1001, "请选择有效的充值金额")

    coin = int(amount_fen / 100 * COIN_PER_YUAN)

    order = RechargeOrder(
        order_no=_gen_order_no(),
        user_id=user_id,
        amount_fen=amount_fen,
        coin=coin,
        status=0,
        remark="",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_my_orders(db: Session, user_id: int, page: int, size: int):
    conditions = [RechargeOrder.user_id == user_id]
    total = int(
        db.scalar(select(func.count()).select_from(RechargeOrder).where(*conditions)) or 0
    )
    rows = list(
        db.scalars(
            select(RechargeOrder)
            .where(*conditions)
            .order_by(RechargeOrder.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def list_orders(db: Session, status: int | None, page: int, size: int):
    conditions = []
    if status is not None:
        conditions.append(RechargeOrder.status == status)

    total = int(
        db.scalar(select(func.count()).select_from(RechargeOrder).where(*conditions)) or 0
    )
    rows = list(
        db.scalars(
            select(RechargeOrder)
            .where(*conditions)
            .order_by(RechargeOrder.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    user_ids = {row.user_id for row in rows}
    users = (
        {u.id: u for u in db.scalars(select(SysUser).where(SysUser.id.in_(user_ids))).all()}
        if user_ids
        else {}
    )

    items = []
    for row in rows:
        user = users.get(row.user_id)
        items.append(
            {
                "id": row.id,
                "order_no": row.order_no,
                "user_id": row.user_id,
                "username": user.username if user else "",
                "nickname": user.nickname if user else "",
                "amount_fen": row.amount_fen,
                "coin": row.coin,
                "status": row.status,
                "created_at": row.created_at,
                "paid_at": row.paid_at,
            }
        )
    return items, total


def confirm_order(db: Session, admin_id: int, order_id: int) -> dict:
    order = db.get(RechargeOrder, order_id)
    if order is None:
        raise BizError(1004, "订单不存在")
    if order.status != 0:
        raise BizError(1001, "该订单已处理，不能重复到账")

    result = db.execute(
        update(RechargeOrder)
        .where(RechargeOrder.id == order_id, RechargeOrder.status == 0)
        .values(
            status=1,
            paid_at=datetime.now(),
            confirmed_by=admin_id,
        )
    )
    if result.rowcount == 0:
        db.rollback()
        raise BizError(1001, "该订单已处理，不能重复到账")

    db.execute(
        update(SysUser)
        .where(SysUser.id == order.user_id)
        .values(coin=SysUser.coin + order.coin)
    )
    db.commit()

    user = db.get(SysUser, order.user_id)
    return {"order_id": order.id, "coin_added": order.coin, "balance": user.coin if user else 0}


def cancel_order(db: Session, order_id: int) -> None:
    order = db.get(RechargeOrder, order_id)
    if order is None:
        raise BizError(1004, "订单不存在")
    if order.status != 0:
        raise BizError(1001, "该订单已处理")
    order.status = 2
    db.commit()


def pay_info() -> dict:
    qr = Path(settings.STATIC_DIR) / "pay" / "wechat.png"
    return {
        "qr_url": "/static/pay/wechat.png" if qr.exists() else None,
        "coin_per_yuan": COIN_PER_YUAN,
        "amounts": ALLOWED_AMOUNTS_FEN,
    }