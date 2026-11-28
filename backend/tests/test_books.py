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
        "/api/v1/admin/users",
        params={"role": "author", "keyword": author["username"]},
        headers=admin["headers"],
    ).json()["data"]
    roles = {item["role"] for item in data["list"]}
    assert roles <= {"author"}
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

# ---------------- 推荐榜口径（回归：曾因两个计数列分裂导致投喂不进榜）----------------


def test_rank_period_accepts_watermelon_alias(client):
    """前端路由用 watermelon 表示投喂西瓜，接口应接受该别名。"""
    resp = client.get(
        "/api/v1/rank/period", params={"metric": "watermelon", "period": "week"}
    )
    assert resp.json()["code"] == 0

    canonical = client.get(
        "/api/v1/rank/period", params={"metric": "recommend", "period": "week"}
    )
    assert canonical.json()["code"] == 0

    # 两种写法结果一致
    alias_ids = [item["book"]["id"] for item in resp.json()["data"]["list"]]
    canon_ids = [item["book"]["id"] for item in canonical.json()["data"]["list"]]
    assert alias_ids == canon_ids


def test_feed_watermelon_updates_counter_and_rank(
    client, author, reader, make_book, approve_book, db
):
    """投喂后：watermelon_count 增加，且周榜「推荐」立刻反映。"""
    from sqlalchemy import text

    book_id = make_book(author, title="投喂测试书")
    approve_book(book_id)

    db.execute(
        text("UPDATE sys_user SET watermelon = 20 WHERE id = :i"), {"i": reader["id"]}
    )
    db.commit()

    def week_value():
        data = client.get(
            "/api/v1/rank/period",
            params={"metric": "recommend", "period": "week", "limit": 50},
        ).json()["data"]["list"]
        for item in data:
            if item["book"]["id"] == book_id:
                return item["value"]
        return 0

    before = week_value()

    # 每本书每天最多 2 个
    resp = client.post(
        f"/api/v1/books/{book_id}/feed-watermelon",
        json={"count": 2},
        headers=reader["headers"],
    )
    assert resp.json()["code"] == 0, resp.json()

    counter = db.execute(
        text("SELECT watermelon_count FROM book WHERE id = :i"), {"i": book_id}
    ).scalar()
    assert counter == 2

    assert week_value() == before + 2


def test_recommend_sort_uses_watermelon_count(client, author, make_book, approve_book, db):
    """总榜 sort=recommend 与 sort=watermelon 应指向同一列。"""
    from sqlalchemy import text

    book_id = make_book(author, title="排序口径书")
    approve_book(book_id)
    db.execute(
        text("UPDATE book SET watermelon_count = 99999 WHERE id = :i"), {"i": book_id}
    )
    db.commit()

    for sort in ("recommend", "watermelon"):
        data = client.get("/api/v1/books", params={"sort": sort, "size": 1}).json()["data"]
        assert data["list"][0]["id"] == book_id, f"sort={sort} 未按 watermelon_count 排序"

def test_subscribe_and_comment_rank_exclude_zero(client, author, make_book, approve_book):
    """订阅榜 / 吐槽榜不应把「值为 0」的书排进来。"""
    book_id = make_book(author, title="零值书")
    approve_book(book_id)

    for sort in ("subscribe", "comment"):
        data = client.get("/api/v1/books", params={"sort": sort, "size": 50}).json()["data"]
        ids = [item["id"] for item in data["list"]]
        assert book_id not in ids, f"sort={sort} 把零值书排进了榜单"
        for item in data["list"]:
            value = item["revenue_coin"] if sort == "subscribe" else item["paragraph_comment_count"]
            assert value > 0, f"sort={sort} 出现值为 0 的条目"