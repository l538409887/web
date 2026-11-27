"""业务异常与全局异常处理器。"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import fail


class BizError(Exception):
    """业务异常：预期内的失败，记 WARNING，不打堆栈。"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizError)
    async def _biz_handler(request: Request, exc: BizError):
        logger.warning("BizError {}: {} path={}", exc.code, exc.message, request.url.path)
        return fail(exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
            msg = f"{loc} {first.get('msg', '')}".strip()
        else:
            msg = "请求参数不合法"
        logger.warning("ValidationError: {} path={}", msg, request.url.path)
        return fail(1001, f"参数校验失败：{msg}")

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(request: Request, exc: StarletteHTTPException):
        mapping = {401: (1002, "登录已失效，请重新登录"), 403: (1003, "没有操作权限"), 404: (1004, "资源不存在")}
        if exc.status_code in mapping:
            code, message = mapping[exc.status_code]
            return fail(code, message)
        return fail(9999, str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception):
        logger.opt(exception=exc).error("未捕获异常 path={}", request.url.path)
        return fail(9999, "服务器内部错误")