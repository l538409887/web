"""内容自动过滤：敏感词检测。

设计要点：
    1. 两级策略
       - block  直接拦截，发布时抛 BizError，用户需改完再发
       - review 放行但转人工（评论置为待审核、章节本就要审）
    2. 防绕过
       匹配前去掉空白与常见分隔符（「加 微 信」「加*微*信」都能命中）
    3. 缓存
       词库在内存里缓存 60 秒，避免每次发布都查库；
       后台改词后调用 invalidate() 立即失效。
"""
import re
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizError
from app.models.sensitive import SensitiveWord

CACHE_TTL = 60
_cache: dict = {"ts": 0.0, "block": [], "review": []}

_SEPARATORS = re.compile(r"[\s\-_*·.,，。!！?？~～|/\\+]+")


def invalidate() -> None:
    """词库变更后立即失效缓存。"""
    _cache["ts"] = 0.0


def load_words(db: Session, force: bool = False) -> dict:
    now = time.time()
    if not force and now - _cache["ts"] < CACHE_TTL:
        return _cache

    rows = db.scalars(
        select(SensitiveWord).where(SensitiveWord.is_active == 1)
    ).all()
    _cache["block"] = [row.word for row in rows if row.level == "block"]
    _cache["review"] = [row.word for row in rows if row.level == "review"]
    _cache["ts"] = now
    return _cache


def normalize(text: str) -> str:
    return _SEPARATORS.sub("", (text or "")).lower()


def scan(db: Session, text: str) -> dict:
    """返回命中的敏感词：{"blocked": [...], "review": [...]}"""
    if not text:
        return {"blocked": [], "review": []}

    words = load_words(db)
    normalized = normalize(text)

    blocked = [w for w in words["block"] if w.lower() in normalized]
    review = [w for w in words["review"] if w.lower() in normalized]
    return {"blocked": blocked, "review": review}


def enforce(db: Session, text: str, scene: str = "内容") -> dict:
    """发布前调用：命中 block 级直接抛错；review 级放行，返回命中项供调用方处理。"""
    result = scan(db, text)
    if result["blocked"]:
        words = "、".join(result["blocked"])
        raise BizError(5001, f"{scene}包含违禁词（{words}），请修改后重试")
    return result


def mask(text: str, words: list[str]) -> str:
    """把命中的词替换成等长星号。"""
    out = text or ""
    for word in words:
        out = re.sub(re.escape(word), "*" * len(word), out, flags=re.IGNORECASE)
    return out


# ---------------------------------------------------------------
# 词库管理（后台）
# ---------------------------------------------------------------

LEVELS = ("block", "review")
CATEGORIES = ("广告", "辱骂", "违禁", "其他")


def list_words(db: Session, keyword: str | None = None, level: str | None = None,
               page: int = 1, size: int = 20):
    from sqlalchemy import func

    conditions = []
    if keyword:
        conditions.append(SensitiveWord.word.like(f"%{keyword.strip()}%"))
    if level:
        conditions.append(SensitiveWord.level == level)

    total = int(
        db.scalar(select(func.count()).select_from(SensitiveWord).where(*conditions)) or 0
    )
    rows = list(
        db.scalars(
            select(SensitiveWord)
            .where(*conditions)
            .order_by(SensitiveWord.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )
    return rows, total


def create_word(db: Session, word: str, level: str, category: str):
    text = (word or "").strip()
    if not text:
        raise BizError(1001, "敏感词不能为空")
    if len(text) > 50:
        raise BizError(1001, "敏感词最多 50 字")
    if level not in LEVELS:
        raise BizError(1001, "level 只能是 block / review")
    if category not in CATEGORIES:
        raise BizError(1001, "分类只能是 广告 / 辱骂 / 违禁 / 其他")

    exists = db.scalar(select(SensitiveWord.id).where(SensitiveWord.word == text))
    if exists:
        raise BizError(1001, "该词已存在")

    row = SensitiveWord(word=text, level=level, category=category, is_active=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    invalidate()
    return row


def update_word(db: Session, word_id: int, **fields):
    row = db.get(SensitiveWord, word_id)
    if row is None:
        raise BizError(1004, "敏感词不存在")

    if "level" in fields and fields["level"]:
        if fields["level"] not in LEVELS:
            raise BizError(1001, "level 只能是 block / review")
        row.level = fields["level"]
    if "category" in fields and fields["category"]:
        if fields["category"] not in CATEGORIES:
            raise BizError(1001, "分类不合法")
        row.category = fields["category"]
    if "is_active" in fields and fields["is_active"] is not None:
        row.is_active = 1 if fields["is_active"] else 0

    db.commit()
    invalidate()
    return row


def delete_word(db: Session, word_id: int) -> None:
    row = db.get(SensitiveWord, word_id)
    if row is None:
        raise BizError(1004, "敏感词不存在")
    db.delete(row)
    db.commit()
    invalidate()