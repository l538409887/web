"""应用入口：uvicorn main:app --reload --port 8000"""
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import setup_logger, trace_id_ctx
from app.core.response import ok

setup_logger()

static_dir = Path(settings.STATIC_DIR)
static_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="基于 Python 的轻量化 Web 小说平台",
    version="1.0.0",
    description="小说阅读平台后端 API。统一响应格式 {code, message, data, trace_id}。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-Id"],
)

register_exception_handlers(app)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    tid = uuid.uuid4().hex[:8]
    token = trace_id_ctx.set(tid)
    request.state.trace_id = tid
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        trace_id_ctx.reset(token)
        raise

    cost = (time.perf_counter() - start) * 1000
    response.headers["X-Trace-Id"] = tid
    logger.info(
        "{} {} -> {} {:.0f}ms",
        request.method,
        request.url.path,
        response.status_code,
        cost,
    )
    if cost > 500:
        logger.warning("慢请求 {} {} {:.0f}ms", request.method, request.url.path, cost)

    trace_id_ctx.reset(token)
    return response


@app.get("/health", tags=["系统"], summary="健康检查")
def health():
    return ok({"status": "up", "env": settings.APP_ENV, "app": settings.APP_NAME})


app.include_router(api_router)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")