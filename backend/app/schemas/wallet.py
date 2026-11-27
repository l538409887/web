"""钱包（签到 / 充值）Schema。"""
from pydantic import BaseModel, Field

from app.schemas.common import APIModel, DateTimeStr


class WalletOut(BaseModel):
    coin: int
    watermelon: int
    signed_today: bool
    total_sign_days: int
    sign_reward: int
    coin_per_yuan: int


class RechargeIn(BaseModel):
    amount_fen: int = Field(gt=0, description="支付金额，单位：分")


class OrderOut(APIModel):
    id: int
    order_no: str
    amount_fen: int
    coin: int
    status: int
    created_at: DateTimeStr | None = None
    paid_at: DateTimeStr | None = None


class AdminOrderItem(OrderOut):
    user_id: int
    username: str = ""
    nickname: str = ""