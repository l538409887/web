"""日志：Loguru 配置 + trace_id 上下文。"""
import sys
from contextvars import ContextVar
from pathlib import Path

from loguru import logger

from app.core.config import settings

trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="-")

LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[trace_id]} | "
    "{name}:{function}:{line} | {message}"
)

_configured = False


def _patcher(record):
    record["extra"].setdefault("trace_id", trace_id_ctx.get())


def setup_logger() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.configure(patcher=_patcher)

    logger.add(
        sys.stderr,
        level="DEBUG" if settings.APP_ENV == "dev" else settings.LOG_LEVEL,
        colorize=True,
        format=LOG_FORMAT,
    )

    common = dict(
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format=LOG_FORMAT,
    )

    logger.add(str(log_dir / "app.log"), level="INFO", **common)
    logger.add(str(log_dir / "error.log"), level="ERROR", **common)
    logger.add(
        str(log_dir / "business.log"),
        level="INFO",
        filter=lambda r: "business" in r["extra"],
        rotation="00:00",
        retention="180 days",
        encoding="utf-8",
        enqueue=True,
        format=LOG_FORMAT,
    )


def get_logger(name: str = "app"):
    return logger.bind(name=name)