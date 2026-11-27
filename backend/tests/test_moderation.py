"""敏感词自动过滤。"""
import pytest


@pytest.fixture()
def word_bank(db):
    """准备两条词：一条拦截级、一条转人工级。"""
    from sqlalchemy import text

    # INSERT IGNORE：多个用例共用词库，重复插入不能报错
    db.execute(
        text(
            "INSERT IGNORE INTO sensitive_word (word, level, category, is_active) "
            "VALUES ('加微信', 'block', '广告', 1)"
        )
    )
    db.execute(
        text(
            "INSERT IGNORE INTO sensitive_word (word, level, category, is_active) "
            "VALUES ('骗子', 'review', '辱骂', 1)"
        )
    )
    db.commit()

    from app.services import moderation_service

    moderation_service.invalidate()
    yield
    moderation_service.invalidate()


@pytest.fixture()
def comment_book(client, author, make_book, approve_book):
    book_id = make_book(author, title="评论测试书")
    approve_book(book_id)
    return book_id


def test_block_word_rejected_in_comment(client, reader, comment_book, word_bank):
    resp = client.post(
        "/api/v1/comments",
        json={"book_id": comment_book, "content": "有兴趣的加微信详聊"},
        headers=reader["headers"],
    )
    assert resp.json()["code"] == 5001
    assert "加微信" in resp.json()["message"]


def test_block_word_bypass_with_separators(client, reader, comment_book, word_bank):
    """「加-微-信」这类绕过写法同样应被拦。"""
    for text in ("加-微-信", "加 微 信", "加*微*信"):
        resp = client.post(
            "/api/v1/comments",
            json={"book_id": comment_book, "content": f"想聊的{text}"},
            headers=reader["headers"],
        )
        assert resp.json()["code"] == 5001, text


def test_review_word_becomes_pending(client, reader, comment_book, word_bank, db):
    from sqlalchemy import text

    resp = client.post(
        "/api/v1/comments",
        json={"book_id": comment_book, "content": "这作者是个骗子"},
        headers=reader["headers"],
    )
    assert resp.json()["code"] == 0, resp.json()
    comment_id = resp.json()["data"]["id"]

    status = db.execute(
        text("SELECT status FROM book_comment WHERE id = :i"), {"i": comment_id}
    ).scalar()
    assert status == 0, "命中转人工词应进入待审核"

    listed = client.get(f"/api/v1/books/{comment_book}/comments").json()["data"]
    ids = [item["id"] for item in listed["list"]]
    assert comment_id not in ids, "待审核评论不应在前台展示"


def test_clean_comment_auto_approved(client, reader, comment_book, word_bank, db):
    from sqlalchemy import text

    resp = client.post(
        "/api/v1/comments",
        json={"book_id": comment_book, "content": "这本书我很喜欢"},
        headers=reader["headers"],
    )
    assert resp.json()["code"] == 0
    comment_id = resp.json()["data"]["id"]

    status = db.execute(
        text("SELECT status FROM book_comment WHERE id = :i"), {"i": comment_id}
    ).scalar()
    assert status == 1

    listed = client.get(f"/api/v1/books/{comment_book}/comments").json()["data"]
    assert comment_id in [item["id"] for item in listed["list"]]


def test_block_word_rejected_in_chapter(
    client, author, make_book, approve_book, word_bank
):
    book_id = make_book(author)
    approve_book(book_id)
    resp = client.post(
        f"/api/v1/author/books/{book_id}/chapters",
        json={"title": "违规章", "content": "扫码领红包，加微信详聊"},
        headers=author["headers"],
    )
    assert resp.json()["code"] == 5001


def test_block_word_rejected_in_book_intro(client, author, category, word_bank):
    resp = client.post(
        "/api/v1/author/books",
        json={
            "title": "违规书名",
            "category_id": category["id"],
            "intro": "本书加微信领取",
            "status": 0,
        },
        headers=author["headers"],
    )
    assert resp.json()["code"] == 5001


def test_paragraph_auto_audit(client, reader, author, make_book, make_chapter, approve_book, word_bank, db):
    """未命中 → 自动通过；命中 review → 待审核。"""
    from sqlalchemy import text

    book_id = make_book(author, title="间贴测试书")
    approve_book(book_id)
    chapter_id = make_chapter(author, book_id, approve=True)

    clean = client.post(
        "/api/v1/paragraph-comments",
        json={
            "book_id": book_id,
            "chapter_id": chapter_id,
            "paragraph_index": 0,
            "content": "这段写得很好",
        },
        headers=reader["headers"],
    ).json()["data"]

    flagged = client.post(
        "/api/v1/paragraph-comments",
        json={
            "book_id": book_id,
            "chapter_id": chapter_id,
            "paragraph_index": 1,
            "content": "作者真是个骗子",
        },
        headers=reader["headers"],
    ).json()["data"]

    clean_audit = db.execute(
        text("SELECT audit_status FROM paragraph_comment WHERE id = :i"),
        {"i": clean["id"]},
    ).scalar()
    flagged_audit = db.execute(
        text("SELECT audit_status FROM paragraph_comment WHERE id = :i"),
        {"i": flagged["id"]},
    ).scalar()

    assert clean_audit == 1, "未命中敏感词应自动通过"
    assert flagged_audit == 0, "命中转人工词应待审核"


def test_admin_word_test_endpoint(client, admin, word_bank):
    resp = client.post(
        "/api/v1/admin/sensitive-words/test",
        json={"text": "加微信了解，骗子勿扰"},
        headers=admin["headers"],
    )
    data = resp.json()["data"]
    assert "加微信" in data["blocked"]
    assert "骗子" in data["review"]
    assert data["would_block"] is True
