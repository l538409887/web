"""认证业务逻辑。"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import SysUser


def register(db: Session, data) -> tuple[SysUser, str, int]:
    if data.password != data.password_confirm:
        raise BizError(1001, "两次输入的密码不一致")

    if db.scalar(select(SysUser.id).where(SysUser.username == data.username)):
        raise BizError(2001, "用户名已被占用")

    if data.email and db.scalar(select(SysUser.id).where(SysUser.email == data.email)):
        raise BizError(2001, "邮箱已被占用")

    user = SysUser(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
        email=data.email or None,
        role="reader",
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token, expires_in = create_access_token(user.id, user.role)
    return user, token, expires_in


def login(db: Session, username: str, password: str) -> tuple[SysUser, str, int]:
    user = db.scalar(select(SysUser).where(SysUser.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise BizError(2002, "用户名或密码错误")
    if user.status == 0:
        raise BizError(2003, "账号已被禁用")

    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    token, expires_in = create_access_token(user.id, user.role)
    return user, token, expires_in


def update_profile(db: Session, user: SysUser, data) -> SysUser:
    if data.nickname is not None:
        user.nickname = data.nickname
    if data.avatar is not None:
        user.avatar = data.avatar
    if data.bio is not None:
        user.bio = data.bio
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: SysUser, old_password: str, new_password: str) -> None:
    if not verify_password(old_password, user.password_hash):
        raise BizError(2004, "原密码不正确")
    if old_password == new_password:
        raise BizError(1001, "新密码不能与原密码相同")
    user.password_hash = hash_password(new_password)
    db.commit()