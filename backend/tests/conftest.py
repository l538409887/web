"""pytest 夹具：把应用整体指向独立的测试库。

关键点：
    1. **不碰生产库**。测试库默认 `novel_platform_test`，与 `novel_platform` 物理隔离。
    2. **必须在 import app 之前**改写 `DATABASE_URL`，
       因为 `app.core.database` 在模块导入时就用该配置建好了 Engine。
    3. 建表直接复用 `db/schema.sql`，避免测试与真实表结构脱节。
    4. 每个测试自己造数据（用户名带随机后缀），互不依赖、可重复执行。

前置（只做一次）：
    mysql -u root -p < db/00_create_test_db.sql
"""
import os
import pathlib
import re
import sys
import uuid

import pytest
from dotenv import load_dotenv

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "novel_platform_test")

_base_url = os.environ.get("DATABASE_URL")
if not _base_url:
    raise RuntimeError(
        "缺少 DATABASE_URL。请先执行：copy backend\\.env.example backend\\.env"
    )

# 把库名换成测试库（其余连接参数沿用 .env）
if not os.environ.get("TEST_DATABASE_URL"):
    os.environ["TEST_DATABASE_URL"] = re.sub(
        r"/([^/?]+)(\?)", rf"/{TEST_DB_NAME}\2", _base_url
    )
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402


def _strip_comments(statement: str) -> str:
    lines = [
        line for line in statement.splitlines() if not line.strip().startswith("--")
    ]
    return "\n".join(lines).strip()


def _schema_statements() -> list[str]:
    sql = (PROJECT_ROOT / "db" / "schema.sql").read_text(encoding="utf-8")
    # 目标库替换 + 去掉 CREATE DATABASE（库由 00_create_test_db.sql 创建）
    sql = sql.replace("novel_platform", TEST_DB_NAME)
    sql = re.sub(r"CREATE DATABASE[^;]+;", "", sql, flags=re.IGNORECASE)

    statements = []
    for chunk in sql.split(";"):
        cleaned = _strip_comments(chunk)
        if cleaned:
            statements.append(cleaned)
    return statements


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """整个会话开始前重建测试库的表结构。

    先无条件清空测试库里的所有表，再执行 schema.sql。
    这样即使上次运行中途失败留下残表，也不会影响本次运行。
    """
    statements = _schema_statements()
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=0")
            existing = conn.exec_driver_sql(
                "SELECT table_name FROM information_schema.tables "
                f"WHERE table_schema = '{TEST_DB_NAME}'"
            ).fetchall()
            for (table_name,) in existing:
                conn.exec_driver_sql(f"DROP TABLE IF EXISTS `{table_name}`")

            for statement in statements:
                conn.exec_driver_sql(statement)
            conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=1")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"测试库初始化失败（{TEST_DB_NAME}）。\n"
            f"请先执行：mysql -u root -p < db/00_create_test_db.sql\n"
            f"原始错误：{exc}"
        ) from exc
    yield


@pytest.fixture(autouse=True)
def disable_rate_limit(monkeypatch):
    """默认关闭限流，避免测试之间互相触发 429。

    需要验证限流的用例自行 monkeypatch 回 True。
    """
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def make_user(client, db):
    """注册一个用户；需要作者/管理员时直接改 role（注册接口只给 reader）。"""

    def _make(role: str = "reader", password: str = "test123456"):
        username = unique(role)
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": username,
                "password": password,
                "password_confirm": password,
                "nickname": username,
            },
        )
        assert resp.status_code == 200, resp.text
        user_id = resp.json()["data"]["user"]["id"]

        if role != "reader":
            db.execute(
                text("UPDATE sys_user SET role = :role WHERE id = :uid"),
                {"role": role, "uid": user_id},
            )
            db.commit()

        login = client.post(
            "/api/v1/auth/login", json={"username": username, "password": password}
        )
        assert login.status_code == 200, login.text
        token = login.json()["data"]["access_token"]

        return {
            "id": user_id,
            "username": username,
            "password": password,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _make


@pytest.fixture()
def category(db):
    name = unique("分类")
    db.execute(
        text("INSERT INTO book_category (name, sort) VALUES (:n, 99)"),
        {"n": name},
    )
    db.commit()
    row = db.execute(
        text("SELECT id FROM book_category WHERE name = :n"), {"n": name}
    ).first()
    return {"id": row[0], "name": name}


@pytest.fixture()
def author(make_user):
    return make_user("author")


@pytest.fixture()
def admin(make_user):
    return make_user("admin")


@pytest.fixture()
def reader(make_user):
    return make_user("reader")


@pytest.fixture()
def make_book(client, category):
    """作者建作品 → 返回 book_id（此时是「未提交」状态）。"""

    def _make(author, title: str | None = None, intro: str = "测试简介"):
        resp = client.post(
            "/api/v1/author/books",
            json={
                "title": title or unique("测试书"),
                "category_id": category["id"],
                "intro": intro,
                "status": 0,
            },
            headers=author["headers"],
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["data"]["id"]

    return _make


@pytest.fixture()
def approve_book(client, admin):
    """把作品推到「已上架」，使其在前台可见。"""

    def _approve(book_id: int, shelf: bool = True):
        resp = client.put(
            f"/api/v1/admin/books/{book_id}/status",
            json={"audit_status": 2},
            headers=admin["headers"],
        )
        assert resp.status_code == 200, resp.text
        if shelf:
            resp = client.put(
                f"/api/v1/admin/books/{book_id}/status",
                json={"shelf_status": 2},
                headers=admin["headers"],
            )
            assert resp.status_code == 200, resp.text

    return _approve


@pytest.fixture()
def make_chapter(client, admin):
    """作者发章节（默认进待审），可选立即审核通过。"""

    def _make(author, book_id: int, title: str = "第1章 测试", content: str = "　　正文内容。", approve: bool = False):
        resp = client.post(
            f"/api/v1/author/books/{book_id}/chapters",
            json={"title": title, "content": content},
            headers=author["headers"],
        )
        assert resp.status_code == 200, resp.text
        chapter_id = resp.json()["data"]["id"]
        if approve:
            resp = client.put(
                f"/api/v1/admin/chapters/{chapter_id}/audit",
                json={"audit_status": 2},
                headers=admin["headers"],
            )
            assert resp.status_code == 200, resp.text
        return chapter_id

    return _make


@pytest.fixture()
def give_coin(db):
    def _give(user_id: int, coin: int = 5000):
        db.execute(
            text("UPDATE sys_user SET coin = :c WHERE id = :i"),
            {"c": coin, "i": user_id},
        )
        db.commit()

    return _give
