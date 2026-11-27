"""应用配置：从 backend/.env 读取，带类型校验。"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "dev"
    APP_NAME: str = "novel-platform"
    APP_PORT: int = 8000

    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 120

    DATABASE_URL: str = (
        "mysql+pymysql://root:root@127.0.0.1:3306/novel_platform?charset=utf8mb4"
    )
    DB_ECHO: bool = False

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "static/covers"
    MAX_UPLOAD_SIZE_MB: int = 2

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()