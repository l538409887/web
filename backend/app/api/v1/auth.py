"""认证接口。"""
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.auth import (
    LoginIn,
    PasswordChangeIn,
    ProfileUpdateIn,
    RegisterIn,
    TokenOut,
    UserBriefOut,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="注册（注册即登录）")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    user, token, expires_in = auth_service.register(db, payload)
    logger.bind(business=True).info("REGISTER user={} username={}", user.id, user.username)
    return ok(
        TokenOut(
            access_token=token,
            expires_in=expires_in,
            user=UserBriefOut.model_validate(user),
        )
    )


@router.post("/login", summary="登录")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user, token, expires_in = auth_service.login(db, payload.username, payload.password)
    logger.bind(business=True).info("LOGIN user={} username={}", user.id, user.username)
    return ok(
        TokenOut(
            access_token=token,
            expires_in=expires_in,
            user=UserBriefOut.model_validate(user),
        )
    )


@router.get("/me", summary="获取当前用户")
def me(user: SysUser = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


@router.put("/me", summary="修改个人资料")
def update_me(
    payload: ProfileUpdateIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = auth_service.update_profile(db, user, payload)
    return ok(UserOut.model_validate(updated))


@router.put("/password", summary="修改密码")
def change_password(
    payload: PasswordChangeIn,
    user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.change_password(db, user, payload.old_password, payload.new_password)
    logger.bind(business=True).info("PASSWORD_CHANGE user={}", user.id)
    return ok(None)


@router.post("/logout", summary="退出登录")
def logout(user: SysUser = Depends(get_current_user)):
    logger.bind(business=True).info("LOGOUT user={}", user.id)
    return ok(None)