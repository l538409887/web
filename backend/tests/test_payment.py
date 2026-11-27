"""付费购买与阅读保护。"""
import pytest


@pytest.fixture()
def paid_book(client, author, admin, make_book, approve_book, make_chapter, db):
    """造一本已上架、已开启付费、含 5 章的书，前 3 章免费。"""
    from sqlalchemy import text

    book_id = make_book(author, title="付费测试书")
    chapter_ids = [
        make_chapter(author, book_id, title=f"第{i}章 内容", content="　　正文。" * 50, approve=True)
        for i in range(1, 6)
    ]
    approve_book(book_id)

    # 开启付费有「字数 ≥ 10 万」的业务门槛。
    # 测试没必要真写 10 万字，直接把统计字段与付费标记写入库，
    # 后面的购买逻辑依然走真实接口。
    db.execute(
        text(
            "UPDATE book SET is_paid = 1, word_count = 120000, price_coin = 600 "
            "WHERE id = :i"
        ),
        {"i": book_id},
    )
    db.commit()

    row = db.execute(
        text("SELECT is_paid, price_coin FROM book WHERE id = :i"), {"i": book_id}
    ).first()
    assert row[0] == 1
    assert row[1] > 0

    return {"id": book_id, "chapters": chapter_ids, "price": row[1]}


def test_free_preview_chapters_readable(client, reader, paid_book):
    """前 3 章免费，无需购买即可阅读。"""
    for chapter_id in paid_book["chapters"][:3]:
        data = client.get(f"/api/v1/chapters/{chapter_id}").json()["data"]
        assert data["locked"] is False
        assert data["content"]


def test_locked_chapter_returns_empty_content(client, reader, paid_book):
    chapter_id = paid_book["chapters"][3]
    data = client.get(f"/api/v1/chapters/{chapter_id}", headers=reader["headers"]).json()["data"]
    assert data["locked"] is True
    assert data["content"] == ""
    assert data["chapter_price"] > 0


def test_purchase_insufficient_balance(client, reader, paid_book, db):
    from sqlalchemy import text

    db.execute(text("UPDATE sys_user SET coin = 0 WHERE id = :i"), {"i": reader["id"]})
    db.commit()

    resp = client.post(
        f"/api/v1/books/{paid_book['id']}/purchase", headers=reader["headers"]
    )
    body = resp.json()
    assert body["code"] == 1001
    # 提示里应带上所需金额
    assert str(paid_book["price"]) in body["message"]


def test_purchase_whole_book_deducts_and_unlocks(
    client, reader, paid_book, give_coin
):
    give_coin(reader["id"], 100000)
    before = client.get("/api/v1/wallet", headers=reader["headers"]).json()["data"]["coin"]

    resp = client.post(
        f"/api/v1/books/{paid_book['id']}/purchase", headers=reader["headers"]
    )
    body = resp.json()
    assert body["code"] == 0, body

    # 返回结构：coin = 本次花费，balance = 扣款后余额
    assert body["data"]["coin"] == paid_book["price"]
    assert body["data"]["balance"] == before - paid_book["price"]

    # 购买后全部章节可读
    for chapter_id in paid_book["chapters"]:
        data = client.get(
            f"/api/v1/chapters/{chapter_id}", headers=reader["headers"]
        ).json()["data"]
        assert data["locked"] is False
        assert data["content"]


def test_purchase_twice_not_double_charged(client, reader, paid_book, give_coin):
    give_coin(reader["id"], 100000)
    client.post(f"/api/v1/books/{paid_book['id']}/purchase", headers=reader["headers"])
    coin_after_first = client.get(
        "/api/v1/wallet", headers=reader["headers"]
    ).json()["data"]["coin"]

    resp = client.post(
        f"/api/v1/books/{paid_book['id']}/purchase", headers=reader["headers"]
    )
    assert resp.json()["code"] != 0
    coin_after_second = client.get(
        "/api/v1/wallet", headers=reader["headers"]
    ).json()["data"]["coin"]
    assert coin_after_first == coin_after_second


def test_buy_single_chapter(client, reader, paid_book, give_coin):
    give_coin(reader["id"], 100000)
    target = paid_book["chapters"][3]

    resp = client.post(
        f"/api/v1/books/{paid_book['id']}/purchase-chapters",
        json={"chapter_ids": [target]},
        headers=reader["headers"],
    )
    assert resp.json()["code"] == 0, resp.json()

    data = client.get(f"/api/v1/chapters/{target}", headers=reader["headers"]).json()["data"]
    assert data["locked"] is False

    # 未买的那一章仍然锁着
    other = paid_book["chapters"][4]
    data = client.get(f"/api/v1/chapters/{other}", headers=reader["headers"]).json()["data"]
    assert data["locked"] is True


def test_paid_chapter_has_watermark(client, reader, paid_book, give_coin):
    """已购正文里应嵌入零宽字符水印。"""
    give_coin(reader["id"], 100000)
    client.post(f"/api/v1/books/{paid_book['id']}/purchase", headers=reader["headers"])

    data = client.get(
        f"/api/v1/chapters/{paid_book['chapters'][3]}", headers=reader["headers"]
    ).json()["data"]
    zero_width = sum(1 for ch in data["content"] if ch in "\u200b\u200c\u200d")
    assert zero_width > 0
    assert data["is_paid"] is True


def test_paid_chapter_no_store_header(client, reader, paid_book, give_coin):
    give_coin(reader["id"], 100000)
    client.post(f"/api/v1/books/{paid_book['id']}/purchase", headers=reader["headers"])

    resp = client.get(
        f"/api/v1/chapters/{paid_book['chapters'][3]}", headers=reader["headers"]
    )
    cache_control = resp.headers.get("cache-control", "")
    assert "no-store" in cache_control


def test_free_book_has_no_watermark(
    client, author, reader, make_book, approve_book, make_chapter
):
    book_id = make_book(author, title="免费书")
    chapter_id = make_chapter(author, book_id, approve=True)
    approve_book(book_id)

    data = client.get(f"/api/v1/chapters/{chapter_id}", headers=reader["headers"]).json()["data"]
    zero_width = sum(1 for ch in data["content"] if ch in "\u200b\u200c\u200d")
    assert zero_width == 0
