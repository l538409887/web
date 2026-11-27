"""审核与上架状态机、章节审核、间贴审核、通知。"""
from tests.conftest import unique


def test_new_book_starts_as_draft(client, author, make_book):
    book_id = make_book(author)
    data = client.get(
        "/api/v1/author/books", headers=author["headers"]
    ).json()["data"]["list"]
    book = next(item for item in data if item["id"] == book_id)
    assert book["audit_status"] == 0
    assert book["shelf_status"] == 0


def test_submit_sets_pending(client, author, make_book):
    book_id = make_book(author)
    resp = client.post(
        f"/api/v1/author/books/{book_id}/submit", headers=author["headers"]
    )
    assert resp.json()["data"]["audit_status"] == 1


def test_duplicate_submit_rejected(client, author, make_book):
    book_id = make_book(author)
    client.post(f"/api/v1/author/books/{book_id}/submit", headers=author["headers"])
    resp = client.post(
        f"/api/v1/author/books/{book_id}/submit", headers=author["headers"]
    )
    assert resp.json()["code"] != 0


def test_cannot_apply_shelf_before_audit(client, author, make_book):
    book_id = make_book(author)
    client.post(f"/api/v1/author/books/{book_id}/submit", headers=author["headers"])
    resp = client.post(
        f"/api/v1/author/books/{book_id}/apply-shelf", headers=author["headers"]
    )
    assert resp.json()["code"] == 1001
    assert "内容审核" in resp.json()["message"]


def test_approved_but_not_shelved_invisible(
    client, author, admin, make_book, approve_book
):
    """审核通过 ≠ 已上架：前台仍然搜不到。"""
    title = unique("不可见")
    book_id = make_book(author, title=title)
    client.post(f"/api/v1/author/books/{book_id}/submit", headers=author["headers"])
    approve_book(book_id, shelf=False)

    resp = client.get("/api/v1/books", params={"keyword": title})
    assert resp.json()["data"]["total"] == 0

    # 上架后才可见
    client.put(
        f"/api/v1/admin/books/{book_id}/status",
        json={"shelf_status": 2},
        headers=admin["headers"],
    )
    resp = client.get("/api/v1/books", params={"keyword": title})
    assert resp.json()["data"]["total"] == 1


def test_full_pipeline_and_notifications(
    client, author, admin, make_book, approve_book
):
    book_id = make_book(author)
    client.post(f"/api/v1/author/books/{book_id}/submit", headers=author["headers"])

    # 管理员驳回
    client.put(
        f"/api/v1/admin/books/{book_id}/status",
        json={"audit_status": 3},
        headers=admin["headers"],
    )
    notices = client.get("/api/v1/user/notices", headers=author["headers"]).json()["data"]
    assert any("审核未通过" in item["title"] for item in notices["list"])

    # 重新提交 → 通过 → 申请上架 → 批准
    client.post(f"/api/v1/author/books/{book_id}/submit", headers=author["headers"])
    approve_book(book_id, shelf=False)

    resp = client.post(
        f"/api/v1/author/books/{book_id}/apply-shelf", headers=author["headers"]
    )
    assert resp.json()["data"]["shelf_status"] == 1

    approve_book(book_id, shelf=True)
    notices = client.get("/api/v1/user/notices", headers=author["headers"]).json()["data"]
    assert any("已上架" in item["title"] for item in notices["list"])
    assert notices["unread"] > 0


def test_pending_chapter_hidden_until_approved(
    client, author, make_book, make_chapter, approve_book
):
    book_id = make_book(author)
    approve_book(book_id)
    chapter_id = make_chapter(author, book_id)

    # 目录里看不到
    catalog = client.get(f"/api/v1/books/{book_id}/chapters").json()["data"]
    assert catalog["total"] == 0
    # 直接访问也拿不到
    resp = client.get(f"/api/v1/chapters/{chapter_id}")
    assert resp.json()["code"] == 3002


def test_chapter_audit_gate(client, author, admin, make_book, make_chapter, approve_book):
    book_id = make_book(author)
    approve_book(book_id)
    chapter_id = make_chapter(author, book_id)

    assert client.get(f"/api/v1/books/{book_id}/chapters").json()["data"]["total"] == 0

    client.put(
        f"/api/v1/admin/chapters/{chapter_id}/audit",
        json={"audit_status": 2},
        headers=admin["headers"],
    )
    assert client.get(f"/api/v1/books/{book_id}/chapters").json()["data"]["total"] == 1
    detail = client.get(f"/api/v1/chapters/{chapter_id}").json()["data"]
    assert detail["content"]


def test_rejected_chapter_stays_hidden(
    client, author, admin, make_book, make_chapter, approve_book
):
    book_id = make_book(author)
    approve_book(book_id)
    chapter_id = make_chapter(author, book_id)

    client.put(
        f"/api/v1/admin/chapters/{chapter_id}/audit",
        json={"audit_status": 3},
        headers=admin["headers"],
    )
    assert client.get(f"/api/v1/books/{book_id}/chapters").json()["data"]["total"] == 0


def test_chapter_audit_queue_filter(
    client, author, admin, make_book, make_chapter
):
    book_id = make_book(author)
    pending_id = make_chapter(author, book_id, title="待审章节")

    queue = client.get(
        "/api/v1/admin/chapters", params={"audit_status": 1}, headers=admin["headers"]
    ).json()["data"]
    assert any(item["id"] == pending_id for item in queue["list"])


def test_paragraph_reject_hides_from_frontend(
    client, author, reader, admin, make_book, make_chapter, approve_book
):
    book_id = make_book(author)
    approve_book(book_id)
    chapter_id = make_chapter(author, book_id, approve=True)

    created = client.post(
        "/api/v1/paragraph-comments",
        json={
            "book_id": book_id,
            "chapter_id": chapter_id,
            "paragraph_index": 0,
            "content": "一条正常的间贴",
        },
        headers=reader["headers"],
    ).json()["data"]

    listed = client.get(f"/api/v1/chapters/{chapter_id}/paragraph-comments").json()["data"]
    assert listed["total"] == 1

    client.put(
        f"/api/v1/admin/paragraph-comments/{created['id']}/audit",
        json={"audit_status": 2},
        headers=admin["headers"],
    )
    listed = client.get(f"/api/v1/chapters/{chapter_id}/paragraph-comments").json()["data"]
    assert listed["total"] == 0


def test_author_cannot_submit_other_author_book(client, author, admin, make_book):
    """越权保护：作者不能操作别人的作品。"""
    from tests.conftest import unique

    username = unique("a2")
    client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "test123456",
            "password_confirm": "test123456",
        },
    )
    users = client.get(
        "/api/v1/admin/users", params={"keyword": username}, headers=admin["headers"]
    ).json()["data"]["list"]
    other_id = users[0]["id"]

    client.put(
        f"/api/v1/admin/users/{other_id}",
        json={"role": "author"},
        headers=admin["headers"],
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "test123456"},
    ).json()["data"]["access_token"]
    other_headers = {"Authorization": f"Bearer {token}"}

    book_id = make_book(author)
    resp = client.post(f"/api/v1/author/books/{book_id}/submit", headers=other_headers)
    assert resp.json()["code"] == 6001
