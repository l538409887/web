"""回填书籍每日统计流水（演示数据）。

背景：`book_daily_stat` 只在真实用户操作时写入，演示库刚建表时是空的，
周榜/月榜会一片空白。这个脚本按每本书的累计热度生成近 N 天的模拟流水。

生成规则（刻意做成「周榜 ≠ 总榜」）：
    - 以累计点击推算日均，再叠加 0.55~1.75 的随机波动
    - 周末略微上扬
    - 每本书有自己的「相位」，让最近 7 天的排名与总榜不同
    - 收藏 ≈ 点击的 6%，投喂 ≈ 点击的 2%，且量级更小

用法：
    cd backend
    .venv\\Scripts\\python.exe scripts\\backfill_stats.py            # 默认 60 天
    .venv\\Scripts\\python.exe scripts\\backfill_stats.py --days 90
    .venv\\Scripts\\python.exe scripts\\backfill_stats.py --reset     # 先清空再生成
"""
import argparse
import math
import pathlib
import random
import sys
from datetime import date, timedelta

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.dialects.mysql import insert  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.book import Book  # noqa: E402
from app.models.stat import BookDailyStat  # noqa: E402


def build_rows(book: Book, days: int) -> list[dict]:
    rng = random.Random(book.id * 7919)  # 每本书固定种子，重复执行结果一致

    # 日均点击：按累计点击推，给一个下限，避免冷门书全是 0
    avg_daily = max(6.0, (book.click_count or 0) / 90.0)
    # 每本书一个相位，制造「最近一周热度不同」的差异
    phase = (book.id * 37) % 100 / 100.0 * math.pi * 2

    rows = []
    today = date.today()
    for offset in range(days):
        day = today - timedelta(days=days - 1 - offset)
        wave = 1.0 + 0.28 * math.sin(phase + offset / 4.5)
        noise = rng.uniform(0.72, 1.3)
        weekend = 1.18 if day.weekday() >= 5 else 1.0

        clicks = max(0, int(avg_daily * wave * noise * weekend))
        collects = max(0, int(clicks * rng.uniform(0.03, 0.09)))
        recs = max(0, int(clicks * rng.uniform(0.005, 0.025)))

        rows.append(
            {
                "book_id": book.id,
                "stat_date": day,
                "clicks": clicks,
                "collects": collects,
                "recommendations": recs,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--reset", action="store_true", help="先清空现有流水")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        books = list(db.scalars(select(Book)).all())
        if not books:
            print("数据库里没有书籍，先执行 db/seed.sql")
            return 1

        if args.reset:
            db.execute(delete(BookDailyStat))
            db.commit()
            print("已清空 book_daily_stat")

        total_rows = 0
        for book in books:
            rows = build_rows(book, args.days)
            if not rows:
                continue
            stmt = insert(BookDailyStat).values(rows)
            stmt = stmt.on_duplicate_key_update(
                clicks=stmt.inserted.clicks,
                collects=stmt.inserted.collects,
                recommendations=stmt.inserted.recommendations,
            )
            db.execute(stmt)
            total_rows += len(rows)

        db.commit()
        print(f"已为 {len(books)} 本书生成 {total_rows} 条日流水（近 {args.days} 天）")

        # 打印一份对照，确认「周榜 ≠ 总榜」
        from app.services import stat_service

        week = stat_service.period_top(db, metric="click", period="week", limit=5)
        month = stat_service.period_top(db, metric="click", period="month", limit=5)
        total = sorted(books, key=lambda b: b.click_count or 0, reverse=True)[:5]

        print("\n最近 7 天点击前 5：")
        for item in week:
            print(f"  {item['book'].title:<12} {item['value']}")
        print("\n最近 30 天点击前 5：")
        for item in month:
            print(f"  {item['book'].title:<12} {item['value']}")
        print("\n累计点击前 5（总榜）：")
        for book in total:
            print(f"  {book.title:<12} {book.click_count}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
