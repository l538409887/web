"""认证与权限。"""
from tests.conftest import unique


def test_register_success(client):
    username = unique("u")
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "abc123456",
            "password_confirm": "abc123456",
            "nickname": "昵称",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["user"]["username"] == username
    assert body["data"]["user"]["role"] == "reader"
    # 注册即登录
    assert body["data"]["access_token"]


def test_register_duplicate_username(client):
    username = unique("dup")
    payload = {
        "username": username,
        "password": "abc123456",
        "password_confirm": "abc123456",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 200
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.json()["code"] != 0


def test_register_password_mismatch(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": unique("m"),
            "password": "abc123456",
            "password_confirm": "abc123457",
        },
    )
    assert resp.json()["code"] != 0


def test_register_invalid_username(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "带中文",
            "password": "abc123456",
            "password_confirm": "abc123456",
        },
    )
    # 触发 Pydantic 校验（422）或业务校验，总之不是 0
    assert resp.status_code != 200 or resp.json()["code"] != 0


def test_login_success_and_me(client, reader):
    resp = client.get("/api/v1/auth/me", headers=reader["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == reader["username"]


def test_login_wrong_password(client, reader):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": reader["username"], "password": "wrong-password"},
    )
    assert resp.json()["code"] != 0
    # 不暴露账号是否存在
    assert "密码" in resp.json()["message"] or "错误" in resp.json()["message"]


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.json()["code"] == 1002


def test_me_with_bad_token(client):
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.json()["code"] == 1002


def test_disabled_user_cannot_login(client, db, make_user):
    from sqlalchemy import text

    user = make_user("reader")
    db.execute(text("UPDATE sys_user SET status = 0 WHERE id = :i"), {"i": user["id"]})
    db.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.json()["code"] == 2003


def test_reader_cannot_access_author_api(client, reader):
    resp = client.get("/api/v1/author/books", headers=reader["headers"])
    assert resp.json()["code"] == 1003


def test_reader_cannot_access_admin_api(client, reader):
    resp = client.get("/api/v1/admin/users", headers=reader["headers"])
    assert resp.json()["code"] == 1003


def test_author_cannot_access_admin_api(client, author):
    resp = client.get("/api/v1/admin/users", headers=author["headers"])
    assert resp.json()["code"] == 1003


def test_change_password(client, make_user):
    user = make_user("reader")
    resp = client.put(
        "/api/v1/auth/password",
        json={"old_password": user["password"], "new_password": "new123456"},
        headers=user["headers"],
    )
    assert resp.json()["code"] == 0

    login = client.post(
        "/api/v1/auth/login",
        json={"username": user["username"], "password": "new123456"},
    )
    assert login.json()["code"] == 0
