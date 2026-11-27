"""访问限流与基础防爬。

三层防护：
    1. 令牌桶限流——按 IP 分类限速（读 / 写 / 登录 / 正文），超限返回 429
    2. UA 拦截——只拦「明确的脚本客户端」，浏览器类 UA 一律放行，避免误伤
    3. 违规封禁——短时间内反复触发限流，临时封禁该 IP

设计取舍：
    - 状态放进程内存：单机部署够用，多实例需要换 Redis（见 README 的取舍说明）
    - UA 判断用「黑名单」而不是「白名单」：白名单会把插件、旧浏览器、内嵌 WebView
      全挡在外面，误伤成本远高于漏放的收益
    - 空 UA 只记录不拦截，同样是为了避免误伤
"""
import time
from dataclasses import dataclass, field

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings

# ---------------- 限流参数（每分钟）----------------
RULES = {
    # 分类: (每分钟上限, 突发容量)
    "auth": (6, 6),        # 登录 / 注册：防撞库
    "chapter": (30, 30),   # 章节正文：防批量抓取
    "write": (20, 20),     # 任何写操作
    "read": (150, 150),    # 普通读接口
}

# 明确的脚本客户端 UA 特征（浏览器 UA 一定包含 Mozilla，先放行）
SCRIPT_UA_MARKERS = (
    "python-requests",
    "python-urllib",
    "python-httpx",
    "scrapy",
    "curl/",
    "wget/",
    "aiohttp",
    "go-http-client",
    "java/",
    "okhttp",
    "postmanruntime",
    "insomnia",
    "httpie",
    "libwww-perl",
    "node-fetch",
    "axios/",
)

SKIP_PREFIXES = ("/static", "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico")

# 违规封禁：5 分钟内触发 20 次 -> 封 10 分钟
BAN_WINDOW = 300
BAN_THRESHOLD = 20
BAN_SECONDS = 600

CLEANUP_EVERY = 500  # 每 500 次调用清理一次过期桶


@dataclass
class _Bucket:
    tokens: float
    ts: float


@dataclass
class _Ban:
    until: float = 0.0
    violations: list = field(default_factory=list)


class RateLimiter:
    def __init__(self, rate_per_minute: int, capacity: int):
        self.rate = rate_per_minute / 60.0
        self.capacity = float(capacity)
        self._buckets: dict[str, _Bucket] = {}
        self._calls = 0

    def allow(self, key: str, cost: float = 1.0) -> bool:
        now = time.monotonic()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(tokens=self.capacity, ts=now)
            self._buckets[key] = bucket
        else:
            bucket.tokens = min(self.capacity, bucket.tokens + (now - bucket.ts) * self.rate)
            bucket.ts = now

        self._calls += 1
        if self._calls % CLEANUP_EVERY == 0:
            self._cleanup(now)

        if bucket.tokens >= cost:
            bucket.tokens -= cost
            return True
        return False

    def _cleanup(self, now: float) -> None:
        stale = [k for k, b in self._buckets.items() if now - b.ts > 600]
        for key in stale:
            self._buckets.pop(key, None)


_limiters = {name: RateLimiter(rate, cap) for name, (rate, cap) in RULES.items()}
_bans: dict[str, _Ban] = {}


def classify(path: str, method: str) -> str:
    if path.startswith("/api/v1/auth/"):
        return "auth"
    if path.startswith("/api/v1/chapters/"):
        return "chapter"
    if method in ("POST", "PUT", "DELETE", "PATCH"):
        return "write"
    return "read"


def _trusted_networks() -> list:
    """把 TRUSTED_PROXIES 解析成网段列表。

    支持单 IP 与 CIDR 两种写法：
        "127.0.0.1,::1"        —— 本机反向代理
        "172.28.0.0/16"        —— Docker 自定义网络
    解析失败的条目直接忽略（配置写错不应该让整个站点 500）。
    """
    import ipaddress

    raw = getattr(settings, "TRUSTED_PROXIES", "") or ""
    networks = []
    for entry in raw.split(","):
        text = entry.strip()
        if not text:
            continue
        try:
            networks.append(ipaddress.ip_network(text, strict=False))
        except ValueError:
            continue
    return networks


def _is_trusted(peer: str) -> bool:
    import ipaddress

    if not peer:
        return False
    try:
        address = ipaddress.ip_address(peer)
    except ValueError:
        # 非 IP（例如测试客户端的 "testclient"）一律视为不可信
        return False
    return any(address in network for network in _trusted_networks())


def client_ip(request: Request) -> str:
    """取客户端 IP，兼顾「直连」与「反向代理」两种部署形态。

    安全要点：
        **只有直连地址本身是可信代理时，才采信转发头。**
        否则任何人都能伪造 `X-Forwarded-For` 把自己的 IP 换掉，
        限流、审计日志、封禁全部失效。

    取法优先级：X-Real-IP（由本项目的 Nginx 配置写入，单值、不可追加）
                > X-Forwarded-For 的第一段 > 直连地址。
    """
    peer = request.client.host if request.client and request.client.host else ""

    if _is_trusted(peer):
        real_ip = (request.headers.get("x-real-ip") or "").strip()
        if real_ip:
            return real_ip

        forwarded = (request.headers.get("x-forwarded-for") or "").split(",")
        if forwarded and forwarded[0].strip():
            return forwarded[0].strip()

    return peer or "unknown"


def is_banned(ip: str) -> bool:
    ban = _bans.get(ip)
    if ban is None:
        return False
    if ban.until and time.monotonic() < ban.until:
        return True
    if ban.until and time.monotonic() >= ban.until:
        _bans.pop(ip, None)
    return False


def record_violation(ip: str) -> int:
    """记一次违规，返回当前窗口内的违规次数。"""
    now = time.monotonic()
    ban = _bans.setdefault(ip, _Ban())
    ban.violations = [t for t in ban.violations if now - t < BAN_WINDOW]
    ban.violations.append(now)
    if len(ban.violations) >= BAN_THRESHOLD:
        ban.until = now + BAN_SECONDS
        ban.violations.clear()
    return len(ban.violations)


def blocked_response(message: str, trace_id: str = "-", retry_after: int = 60) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"code": 429, "message": message, "data": None, "trace_id": trace_id},
        headers={"Retry-After": str(retry_after)},
    )


async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(SKIP_PREFIXES):
        return await call_next(request)

    ip = client_ip(request)
    tid = getattr(request.state, "trace_id", "-")

    if is_banned(ip):
        logger.warning("BAN 已封禁 IP 访问 path={} ip={}", path, ip)
        return blocked_response("访问过于频繁，已被临时限制，请稍后再试", tid, BAN_SECONDS)

    # UA 检查：只拦明确的脚本客户端
    ua = (request.headers.get("user-agent") or "").strip()
    ua_lower = ua.lower()
    if ua and "mozilla" not in ua_lower:
        for marker in SCRIPT_UA_MARKERS:
            if marker in ua_lower:
                times = record_violation(ip)
                logger.warning(
                    "UA_BLOCK path={} ip={} ua={} violations={}", path, ip, ua[:80], times
                )
                return blocked_response("检测到自动化访问，请使用浏览器访问本站", tid)

    category = classify(path, request.method)
    if not _limiters[category].allow(f"{category}:{ip}"):
        times = record_violation(ip)
        logger.warning(
            "RATE_LIMIT category={} path={} ip={} violations={}", category, path, ip, times
        )
        return blocked_response("请求过于频繁，请稍后再试", tid)

    return await call_next(request)
