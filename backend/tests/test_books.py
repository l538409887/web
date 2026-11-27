"""书籍浏览、举报、后台筛选、榜单。"""
from tests.conftest import unique


def test_book_list_public(client, author, make_book, approve_book):
    title = unique("公开书")
    book_id = make_book(author, title=title)
    approve_book(book_id)

    data = client.get("/api/v1/books", params={"keyword": title}).json()["data"]
    assert data["total"] == 1
    assert data["list"][0]["id"] == book_id


def test_book_detail(client, author, make_book, approve_book):
    book_id = make_book(author)
    approve_book(book_id)
    data = client.get(f"/api/v1/books/{book_id}").json()["data"]
    assert data["id"] == book_id
    assert data["title"]


def test_home_aggregate(client):
    data = client.get("/api/v1/home").json()["data"]
    for key in ("banners", "categories", "latest", "ranks", "sections"):
        assert key in data


def test_report_needs_login(client, author, make_book, approve_book, reader):
    book_id = make_book(author)
    approve_book(book_id)
    comment = client.post(
        "/api/v1/comments",
        json={"book_id": book_id, "content": "一条评论"},
        headers=reader["headers"],
    ).json()["data"]

    resp = client.post(
        "/api/v1/reports",
        json={"target_type": "book_comment", "target_id": comment["id"], "reason": "辱骂攻击"},
    )
    assert resp.json()["code"] == 1002


def test_report_and_admin_queue(
    client, author, reader, admin, make_user, make_book, approve_book
):
    book_id = make_book(author)
    approve_book(book_id)

    # 自己不能举报自己，所以由另一个用户来举报
    reporter = make_user("reader")
    comment = client.post(
        "/api/v1/comments",
        json={"book_id": book_id, "content": "待举报的评论"},
        headers=reader["headers"],
    ).json()["data"]

    reasons = client.get("/api/v1/reports/reasons").json()["data"]
    reason = reasons[0]

    resp = client.post(
        "/api/v1/reports",
        json={
            "target_type": "book_comment",
            "target_id": comment["id"],
            "reason": reason,
        },
        headers=reporter["headers"],
    )
    assert resp.json()["code"] == 0, resp.json()

    # 同一人重复举报应被拒绝
    dup = client.post(
        "/api/v1/reports",
        json={
            "target_type": "book_comment",
            "target_id": comment["id"],
            "reason": reason,
        },
        headers=reporter["headers"],
    )
    assert dup.json()["code"] != 0

    queue = client.get("/api/v1/admin/reports", headers=admin["headers"]).json()["data"]
    assert queue["total"] >= 1

    # 被举报评论能单独筛出来
    reported = client.get(
        "/api/v1/admin/comments", params={"reported": True}, headers=admin["headers"]
    ).json()["data"]
    assert comment["id"] in [item["id"] for item in reported["list"]]


def test_admin_user_role_filter(client, admin, make_user):
    author = make_user("author")
    data = client.get(
        "/api/v1/admin/users", params={"role": "author"}, headers=admin["headers"]
    ).json()["data"]
    roles = {item["role"] for item in data["list"]}
    assert roles == {"author"}
    assert author["id"] in [item["id"] for item in data["list"]]


def test_rank_period_validation(client):
    assert client.get("/api/v1/rank/period", params={"metric": "bad"}).json()["code"] == 1001
    assert client.get("/api/v1/rank/period", params={"period": "year"}).json()["code"] == 1001


def test_rank_period_returns_shape(client, author, make_book, approve_book, admin):
    """造点点击流水后，周榜应能返回结构正确的结果。"""
    book_id = make_book(author, title=unique("榜单书"))
    approve_book(book_id)
    for _ in range(3):
        client.get(f"/api/v1/books/{book_id}")

    data = client.get(
        "/api/v1/rank/period", params={"metric": "click", "period": "week", "limit": 10}
    ).json()["data"]
    assert data["period"] == "week"
    assert isinstance(data["list"], list)
    for item in data["list"]:
        assert item["rank"] >= 1
        assert "book" in item


def test_follow_author(client, author, reader):
    resp = client.post(
        f"/api/v1/authors/{author['id']}/follow", headers=reader["headers"]
    )
    assert resp.json()["code"] == 0

    follows = client.get("/api/v1/user/follows", headers=reader["headers"]).json()["data"]
    assert author["id"] in [item["id"] for item in follows["list"]]

    # 重复关注不报错也不重复
    resp = client.post(
        f"/api/v1/authors/{author['id']}/follow", headers=reader["headers"]
    )
    assert resp.json()["code"] in (0, 1001)

    client.delete(f"/api/v1/authors/{author['id']}/follow", headers=reader["headers"])
    follows = client.get("/api/v1/user/follows", headers=reader["headers"]).json()["data"]
    assert author["id"] not in [item["id"] for item in follows["list"]]
