"""认证相关 Schema。"""
from pydantic import BaseModel, Field

from app.schemas.common import APIModel, DateTimeStr


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=32)
    password_confirm: str
    email: str | None = Field(default=None, max_length=128)
    nickname: str | None = Field(default=None, max_length=20)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=64)


class UserBriefOut(APIModel):
    id: int
    username: str
    nickname: str
    avatar: str = ""
    role: str


class UserOut(UserBriefOut):
    email: str | None = None
    bio: str = ""
    created_at: DateTimeStr | None = None
    last_login_at: DateTimeStr | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserBriefOut


class ProfileUpdateIn(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=20)
    avatar: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=120)


class PasswordChangeIn(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=6, max_length=32)