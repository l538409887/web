"""生成 docs/03-数据库设计说明书.md 与 docs/04-接口文档.md。

事实部分（表结构、索引、外键、接口清单）全部从**权威来源**读取：
    - 数据库：information_schema（表、字段、索引、外键、注释）
    - 接口：FastAPI 的 openapi.json（路径、方法、摘要、参数）

叙述部分（设计取舍、状态约定、错误码说明）以常量形式固化在本文件里，
所以「重新生成」不会丢失人工撰写的章节。

用法：
    cd backend
    .venv\\Scripts\\python.exe scripts\\gen_docs.py
"""
import json
import pathlib
import sys
from datetime import datetime

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

DOCS_DIR = PROJECT_ROOT / "docs"
DB_NAME = "novel_platform"

# 表分组：便于阅读，也说明模块划分
TABLE_GROUPS = [
    ("账号与权限", ["sys_user"]),
    ("书籍与内容", ["book", "book_category", "book_tag", "book_tag_rel", "book_chapter"]),
    ("读者行为", ["user_bookshelf", "reading_history", "book_comment", "book_vote"]),
    ("付费与钱包", ["book_purchase", "chapter_purchase", "recharge_order", "user_sign_in"]),
    ("互动与治理", [
        "paragraph_comment", "paragraph_reaction", "content_report",
        "book_watermelon_log", "sensitive_word", "user_notice", "site_notice",
    ]),
    ("统计与关注", ["book_daily_stat", "author_follow"]),
]

# 状态字段约定（手工维护，自动生成容易失真）
STATE_FIELDS = """\
| 表.字段 | 取值 | 说明 |
|---|---|---|
| `book.audit_status` | 0 未提交 / 1 待审核 / 2 审核通过 / 3 审核未通过 | 内容审核流水线第一阶段 |
| `book.shelf_status` | 0 未上架 / 1 上架审核中 / 2 已上架 / 3 上架未通过 | 第二阶段，**审核通过 ≠ 已上架** |
| `book.is_paid` | 0 免费 / 1 付费 | 字数 ≥ 10 万才能开启 |
| `book_chapter.audit_status` | 0 草稿 / 1 待审核 / 2 已通过 / 3 未通过 | 章节**先审后发** |
| `book_chapter.status` | 0 已隐藏 / 1 正常 | 逻辑删除 |
| `paragraph_comment.audit_status` | 0 待审核 / 1 已通过 / 2 已驳回 | 间贴**先发后审**：待审也展示，驳回才隐藏 |
| `paragraph_comment.status` | 0 已隐藏 / 1 正常 | 与举报处理联动 |
| `content_report.status` | 0 待处理 / 1 已忽略 / 2 已处理（内容已隐藏） | 举报队列 |
| `recharge_order.status` | 0 待支付 / 1 已到账 / 2 已取消 | 人工确认到账 |
| `sys_user.role` | reader / author / admin | 三端权限基础 |

> **可见性规则（三处统一到模型 hybrid 属性）**
> - 书籍前台可见：`audit_status = 2 AND shelf_status = 2` → `Book.is_online`
> - 章节可读：`status = 1 AND audit_status = 2` → `BookChapter.is_visible`
> - 间贴展示：`status = 1 AND audit_status != 2` → `ParagraphComment.is_visible`
"""

REDUNDANT_FIELDS = """\
为避免每次列表查询都做聚合，`book` 表冗余了几个统计字段，由
`book_service.recalc_stats()` 统一维护：

| 冗余字段 | 真实来源 | 触发重算的时机 |
|---|---|---|
| `chapter_count` | `COUNT(book_chapter WHERE status=1)` | 章节新增 / 修改 / 逻辑删除 / 批量导入 |
| `word_count` | `SUM(book_chapter.word_count)` | 同上 |
| `last_chapter_id` / `last_chapter_title` | 最新章节 | 同上 |
| `last_update_at` | 最新章节创建时间 | 同上 |
| `price_coin` | `ceil(word_count × 5 / 1000)` | 同上，且仅 `is_paid=1` 时更新 |

另外两个计数器是**增量维护**而非重算：

| 字段 | 维护方式 |
|---|---|
| `book.paragraph_comment_count` | 顶层间贴发布 +1、隐藏/删除 -1；**回复不计入** |
| `book.watermelon_count` | 投喂时 +n |
| `book.revenue_coin` | 购买成交时 +金额 |

> ⚠️ 一致性风险：直接改数据库（如手工 DELETE 章节）不会触发重算，
> 需手动调用 `recalc_stats` 或重跑统计脚本。
"""

INDEX_NOTES = """\
| 索引 | 表 | 解决的问题 |
|---|---|---|
| `uk_user_date` | user_sign_in | 同一用户同一天只能签到一次（并发安全） |
| `uk_user_book` | book_purchase | 防重复购买整本 |
| `uk_user_chapter` | chapter_purchase | 防重复购买单章 |
| `uk_target_reporter` | content_report | 同一人对同一内容只能举报一次 |
| `uk_book_date` | book_daily_stat | 每日统计幂等 upsert 的前提 |
| `uk_user_author` | author_follow | 防重复关注 |
| `uk_word` | sensitive_word | 词表去重 |
| `idx_status_created` | content_report | 后台举报队列按状态+时间翻页 |
| `idx_para` | paragraph_comment | 阅读页按章节+段落批量取间贴 |
| `idx_user_read` | user_notice | 顶栏未读数与消息列表 |
| `is_recommend` | book | 首页轮播/推荐位筛选 |
"""

MIGRATIONS = """\
| 版本 | 文件 | 内容 |
|---|---|---|
| 000 | `db/schema.sql` | 初始 10 张表 |
| 001 | `db/migrations/001_wallet.sql` | 签到、充值订单、用户余额 |
| 002 | `002_paid_watermelon_paragraph.sql` | 付费、投喂西瓜、间贴 |
| 003 | `003_chapter_purchase.sql` | 按章购买 |
| 004 | `004_paragraph_reply.sql` | 间贴回复（自关联） |
| 005 | `005_site_notice.sql` | 站点公告 |
| 006 | `006_author_follow.sql` | 作者关注 |
| 007 | `007_content_report.sql` | 内容举报（从 reaction 中拆出） |
| 008 | `008_audit_shelf.sql` | 审核四态 + 上架四态 |
| 009 | `009_user_notice.sql` | 站内通知 |
| 010 | `010_sensitive_word.sql` | 敏感词库 |
| 011 | `011_book_daily_stat.sql` | 每日统计（周/月榜数据源） |
| 012 | `012_notice_cover.sql` | 公告封面图 |
"""

ERROR_CODES = """\
| code | HTTP | 含义 |
|---|---|---|
| 0 | 200 | 成功 |
| 1001 | 422 | 参数或业务规则不满足 |
| 1002 | 401 | 未登录 / Token 失效 |
| 1003 | 403 | 无权限 |
| 1004 | 404 | 资源不存在 |
| 1005 | 429 | 请求过于频繁 |
| 2001 | 400 | 注册参数错误 |
| 2002 | 400 | 用户名或密码错误 |
| 2003 | 403 | 账号被禁用 |
| 2004 | 400 | 旧密码错误 |
| 3001 | 404 | 书籍不存在或已下架 |
| 3002 | 404 | 章节不存在 |
| 3003 | 400 | 章节不属于该书籍 |
| 3004 | 402 | 付费内容未购买 |
| 4001 | 400 | 上传文件不合法 |
| 5001 | 400 | 评论/内容校验失败 |
| 5002 | 403 | 无权删除他人内容 |
| 6001 | 403 | 非本人作品 |
| 9001 | 500 | 业务异常 |
| 9999 | 500 | 未捕获异常 |
"""


def q(sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()


def fetch_tables() -> list[str]:
    rows = q(
        f"SELECT table_name FROM information_schema.tables "
        f"WHERE table_schema='{DB_NAME}' ORDER BY table_name"
    )
    return [r[0] for r in rows]


def fetch_table_comment(table: str) -> str:
    rows = q(
        f"SELECT table_comment FROM information_schema.tables "
        f"WHERE table_schema='{DB_NAME}' AND table_name='{table}'"
    )
    return (rows[0][0] or "") if rows else ""


def fetch_columns(table: str) -> list[dict]:
    rows = q(
        f"SELECT column_name, column_type, is_nullable, column_default, "
        f"column_key, extra, column_comment "
        f"FROM information_schema.columns "
        f"WHERE table_schema='{DB_NAME}' AND table_name='{table}' "
        f"ORDER BY ordinal_position"
    )
    return [
        {
            "name": r[0],
            "type": r[1],
            "nullable": r[2],
            "default": r[3],
            "key": r[4],
            "extra": r[5],
            "comment": r[6],
        }
        for r in rows
    ]


def fetch_indexes(table: str) -> list[dict]:
    rows = q(
        f"SELECT index_name, non_unique, GROUP_CONCAT(column_name ORDER BY seq_in_index) "
        f"FROM information_schema.statistics "
        f"WHERE table_schema='{DB_NAME}' AND table_name='{table}' "
        f"GROUP BY index_name, non_unique ORDER BY index_name"
    )
    return [
        {"name": r[0], "unique": int(r[1]) == 0, "columns": r[2]} for r in rows
    ]


def fetch_fks(table: str) -> list[dict]:
    rows = q(
        f"SELECT constraint_name, column_name, referenced_table_name, referenced_column_name "
        f"FROM information_schema.key_column_usage "
        f"WHERE table_schema='{DB_NAME}' AND table_name='{table}' "
        f"AND referenced_table_name IS NOT NULL ORDER BY constraint_name"
    )
    return [
        {"name": r[0], "column": r[1], "ref_table": r[2], "ref_column": r[3]}
        for r in rows
    ]


def cell(value) -> str:
    if value is None:
        return "—"
    text_value = str(value).replace("|", "\\|").replace("\n", " ")
    return text_value if text_value else "—"


def build_db_doc() -> str:
    tables = fetch_tables()
    total = len(tables)

    lines: list[str] = []
    lines.append("# 数据库设计说明书")
    lines.append("")
    lines.append("> 基于 Python 的轻量化 Web 小说平台 · 数据库：MySQL 8.0（utf8mb4）")
    lines.append(">")
    lines.append(f"> 本文档由 `backend/scripts/gen_docs.py` 从 `information_schema` 自动生成，")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}。**请勿手工修改**，")
    lines.append("> 改完表结构后重新生成即可。叙述性章节固化在生成脚本里。")
    lines.append("")

    lines.append("## 一、概览")
    lines.append("")
    lines.append(f"当前库 `{DB_NAME}` 共 **{total} 张表**，按业务域分组如下。")
    lines.append("")
    lines.append("| 分组 | 表 |")
    lines.append("|---|---|")
    grouped = {name for _, names in TABLE_GROUPS for name in names}
    for group_name, names in TABLE_GROUPS:
        existing = [f"`{n}`" for n in names if n in tables]
        if existing:
            lines.append(f"| {group_name} | {' '.join(existing)} |")
    others = [f"`{t}`" for t in tables if t not in grouped]
    if others:
        lines.append(f"| 其他 | {' '.join(others)} |")
    lines.append("")
    lines.append("核心关系：")
    lines.append("")
    lines.append("```")
    lines.append("sys_user 1──N book           (作者)")
    lines.append("book     1──N book_chapter   (章节)")
    lines.append("book     1──N book_comment   (书评，自关联一层回复)")
    lines.append("book     1──N user_bookshelf (书架)")
    lines.append("book     1──N book_purchase / chapter_purchase (购买)")
    lines.append("book_chapter 1──N paragraph_comment (间贴，按段落定位)")
    lines.append("book     1──N book_daily_stat (每日统计 → 周/月榜)")
    lines.append("sys_user 1──N user_notice     (站内通知)")
    lines.append("content_report 多态指向 book_comment / paragraph_comment")
    lines.append("```")
    lines.append("")

    lines.append("## 二、状态字段约定")
    lines.append("")
    lines.append(STATE_FIELDS)

    lines.append("## 三、数据表明细")
    lines.append("")
    for table in tables:
        comment = fetch_table_comment(table)
        columns = fetch_columns(table)
        indexes = fetch_indexes(table)
        fks = fetch_fks(table)

        lines.append(f"### {table}" + (f" — {comment}" if comment else ""))
        lines.append("")

        lines.append("| 字段 | 类型 | 可空 | 默认 | 说明 |")
        lines.append("|---|---|---|---|---|")
        for col in columns:
            flag = "是" if col["nullable"] == "YES" else "否"
            lines.append(
                f"| `{col['name']}`{' 🔑' if col['key'] == 'PRI' else ''} "
                f"| {col['type']} | {flag} | {cell(col['default'])} | {cell(col['comment'])} |"
            )
        lines.append("")

        if indexes:
            lines.append("索引：" + "、".join(
                f"`{i['name']}`" + ("（唯一）" if i["unique"] else "") + f"({i['columns']})"
                for i in indexes
            ))
            lines.append("")
        if fks:
            lines.append("外键：" + "、".join(
                f"`{f['column']}` → `{f['ref_table']}.{f['ref_column']}`" for f in fks
            ))
            lines.append("")

    lines.append("## 四、冗余字段与一致性")
    lines.append("")
    lines.append(REDUNDANT_FIELDS)

    lines.append("## 五、关键索引设计")
    lines.append("")
    lines.append(INDEX_NOTES)

    lines.append("## 六、迁移历史")
    lines.append("")
    lines.append(MIGRATIONS)

    return "\n".join(lines) + "\n"


def load_openapi() -> dict:
    from main import app

    return app.openapi()


def collect_dependencies() -> dict[tuple[str, str], list[str]]:
    """从各模块的 APIRouter 里取出每个 (path, method) 的依赖函数名。

    不能遍历 app.routes：当前 FastAPI 版本会把 include_router 进来的路由
    包成 _IncludedRouter，拿不到叶子节点的 dependant。
    逐模块遍历 APIRouter 更直接，route.path 已包含模块前缀，
    全路径 = "/api/v1" + route.path。
    """
    import importlib
    import pkgutil

    from fastapi.routing import APIRoute

    import app.api.v1 as v1_pkg

    result: dict[tuple[str, str], list[str]] = {}

    def walk(dependant, acc: list[str]) -> None:
        for sub in dependant.dependencies:
            call = getattr(sub, "call", None)
            if call is not None:
                acc.append(f"{getattr(call, '__module__', '')}.{getattr(call, '__name__', '')}")
            walk(sub, acc)

    for mod_info in pkgutil.iter_modules(v1_pkg.__path__):
        if mod_info.name == "__init__":
            continue
        module = importlib.import_module(f"app.api.v1.{mod_info.name}")
        router = getattr(module, "router", None)
        if router is None:
            continue
        for route in getattr(router, "routes", []):
            if not isinstance(route, APIRoute):
                continue
            names: list[str] = []
            walk(route.dependant, names)
            full_path = "/api/v1" + route.path
            for method in route.methods or []:
                result[(full_path, method.upper())] = names
    return result


# 可选登录的依赖：公开接口但登录后能看到更多信息（如是否已收藏）
_OPTIONAL_DEPS = ("app.core.deps.get_current_user_optional",)


def auth_label(path: str, names: list[str]) -> str:
    required = [
        n for n in names if "app.core.deps" in n and n not in _OPTIONAL_DEPS
    ]
    if not required:
        return "公开"
    if path.startswith("/api/v1/admin"):
        return "需管理员"
    if path.startswith("/api/v1/author"):
        return "需作者"
    return "需登录"


TAG_ORDER = [
    "认证", "首页", "书籍", "章节", "分类", "评论", "书架", "钱包",
    "互动", "举报", "榜单", "作者", "作者中心", "用户中心", "公告",
    "管理后台", "上传", "系统",
]


def build_api_doc() -> str:
    spec = load_openapi()
    paths = spec.get("paths", {})

    deps = collect_dependencies()

    # 按 tag 聚合
    tagged: dict[str, list[dict]] = {}
    for path, methods in paths.items():
        for method, meta in methods.items():
            if method not in ("get", "post", "put", "delete", "patch"):
                continue
            tags = meta.get("tags") or ["其他"]
            tag = tags[0]
            tagged.setdefault(tag, []).append(
                {
                    "path": path,
                    "method": method.upper(),
                    "summary": meta.get("summary", ""),
                    "params": meta.get("parameters", []),
                    "body": meta.get("requestBody"),
                    "security": meta.get("security"),
                    "desc": meta.get("description", ""),
                    "auth": auth_label(path, deps.get((path, method.upper()), [])),
                }
            )

    order = [t for t in TAG_ORDER if t in tagged] + [
        t for t in sorted(tagged) if t not in TAG_ORDER
    ]
    total = sum(len(v) for v in tagged.values())

    lines: list[str] = []
    lines.append("# 接口文档")
    lines.append("")
    lines.append("> 基于 Python 的轻量化 Web 小说平台 · 后端 HTTP API")
    lines.append(">")
    lines.append(f"> 本文档由 `backend/scripts/gen_docs.py` 从 FastAPI 的 `openapi.json` 自动生成，")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}。**请勿手工修改**。")
    lines.append("")

    lines.append("## 一、通用约定")
    lines.append("")
    lines.append("**Base URL**：`http://127.0.0.1:8000/api/v1`")
    lines.append("")
    lines.append("**统一响应结构**")
    lines.append("")
    lines.append("```json")
    lines.append('{ "code": 0, "message": "ok", "data": { }, "trace_id": "a1b2c3d4" }')
    lines.append("```")
    lines.append("")
    lines.append("- `code = 0` 表示成功，非 0 为业务错误码（见第四节）")
    lines.append("- `trace_id` 与响应头 `X-Trace-Id`、服务端日志一一对应，便于排查")
    lines.append("")
    lines.append("**鉴权**")
    lines.append("")
    lines.append("- 登录后返回 JWT，后续请求带 `Authorization: Bearer <token>`")
    lines.append("- 「鉴权」列取值：公开 / 需登录 / 需作者 / 需管理员")
    lines.append("")
    lines.append("**分页**")
    lines.append("")
    lines.append("列表接口统一接受 `page`（从 1 开始）与 `size`，返回 "
                 "`{list, total, page, size, pages}`。")
    lines.append("")
    lines.append("**限流与防爬**")
    lines.append("")
    lines.append("| 分类 | 上限（每分钟/IP） |")
    lines.append("|---|---|")
    lines.append("| 认证接口 | 6 |")
    lines.append("| 章节正文 | 30（另按账号 40） |")
    lines.append("| 写操作 | 20 |")
    lines.append("| 其他读接口 | 150 |")
    lines.append("")
    lines.append("超限返回 `429` 并带 `Retry-After`；UA 命中脚本特征（curl / requests 等）"
                 "且不含 `Mozilla` 时直接拒绝。")
    lines.append("")
    lines.append("**可见性规则**")
    lines.append("")
    lines.append("- 书籍：`audit_status=2 且 shelf_status=2` 才出现在前台")
    lines.append("- 章节：`status=1 且 audit_status=2` 才可读，否则返回 `3002`")
    lines.append("- 付费章节未购买：返回 `locked=true` 且正文为空，不报错")
    lines.append("")

    lines.append("## 二、接口总览")
    lines.append("")
    lines.append(f"共 **{total} 个接口**，按模块分组：")
    lines.append("")
    for tag in order:
        items = tagged[tag]
        lines.append(f"**{tag}**（{len(items)}）")
        lines.append("")
        lines.append("| 方法 | 路径 | 鉴权 | 说明 |")
        lines.append("|---|---|---|---|")
        for item in items:
            lines.append(
                f"| `{item['method']}` | `{item['path']}` | {item['auth']} | {item['summary']} |"
            )
        lines.append("")

    lines.append("## 三、接口明细")
    lines.append("")
    for tag in order:
        lines.append(f"### {tag}")
        lines.append("")
        for item in tagged[tag]:
            auth = item["auth"]
            lines.append(f"#### `{item['method']} {item['path']}`")
            lines.append("")
            if item["summary"]:
                lines.append(f"{item['summary']}")
                lines.append("")
            lines.append(f"- 鉴权：{auth}")

            path_params = [p for p in item["params"] if p.get("in") == "path"]
            query_params = [p for p in item["params"] if p.get("in") == "query"]
            if path_params:
                lines.append(
                    "- 路径参数：" + "、".join(
                        f"`{p['name']}`" for p in path_params
                    )
                )
            if query_params:
                parts = []
                for p in query_params:
                    schema = p.get("schema", {}) or {}
                    default = schema.get("default", "—")
                    parts.append(f"`{p['name']}`（默认 {default}）")
                lines.append("- 查询参数：" + "、".join(parts))
            if item["body"]:
                ref = (
                    item["body"].get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                    .get("$ref", "")
                )
                if ref:
                    lines.append(f"- 请求体：`{ref.split('/')[-1]}`")
                else:
                    lines.append("- 请求体：JSON")
            lines.append("")

    lines.append("## 四、错误码")
    lines.append("")
    lines.append(ERROR_CODES)

    return "\n".join(lines) + "\n"


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    db_doc = build_db_doc()
    (DOCS_DIR / "03-数据库设计说明书.md").write_text(db_doc, encoding="utf-8")
    print(f"已生成 docs/03-数据库设计说明书.md（{len(db_doc.splitlines())} 行）")

    api_doc = build_api_doc()
    (DOCS_DIR / "04-接口文档.md").write_text(api_doc, encoding="utf-8")
    print(f"已生成 docs/04-接口文档.md（{len(api_doc.splitlines())} 行）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
