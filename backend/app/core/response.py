"""统一响应结构：{code, message, data, trace_id}。"""
from typing import Any

from fastapi.responses import JSONResponse

from app.core.logger import trace_id_ctx

HTTP_STATUS: dict[int, int] = {
    0: 200,
    1001: 422,
    1002: 401,
    1003: 403,
    1004: 404,
    1005: 429,
    2001: 400,
    2002: 400,
    2003: 403,
    2004: 400,
    3001: 404,
    3002: 404,
    3003: 400,
    3004: 402,
    4001: 400,
    5001: 400,
    5002: 403,
    6001: 403,
    9001: 500,
    9999: 500,
}


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "trace_id": trace_id_ctx.get(),
    }


def fail(code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_STATUS.get(code, 500),
        content={
            "code": code,
            "message": message,
            "data": None,
            "trace_id": trace_id_ctx.get(),
        },
    )