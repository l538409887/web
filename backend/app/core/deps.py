"""依赖注入：数据库会话、当前用户、角色校验。"""
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BizError
from app.core.security import decode_token
from app.models.user import SysUser


def _load_user(authorization: str | None, db: Session) -> SysUser | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    return db.get(SysUser, user_id)


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> SysUser | None:
    """可选登录：带上 Token 就解析，不带也不报错。"""
    return _load_user(authorization, db)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> SysUser:
    if not authorization:
        raise BizError(1002, "登录已失效，请重新登录")
    user = _load_user(authorization, db)
    if user is None:
        raise BizError(1002, "登录已失效，请重新登录")
    if user.status == 0:
        raise BizError(2003, "账号已被禁用")
    return user


def require_role(*roles: str):
    def _checker(user: SysUser = Depends(get_current_user)) -> SysUser:
        if user.role not in roles:
            raise BizError(1003, "没有操作权限")
        return user

    return _checker