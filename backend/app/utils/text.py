"""文本处理工具：自动分章、字数统计。"""
import re

_CHAPTER_RE = re.compile(
    r"^[ \t]*第[ \t]*[0-9０-９一二三四五六七八九十百千零两]+[ \t]*[章回节卷][^\n]*$",
    re.MULTILINE,
)


def split_chapters(raw_text: str) -> list[tuple[str, str]]:
    """把整段文本按「第N章」切分为 [(标题, 正文), ...]。

    找不到章节标记时，退化为「整段作为一章」，标题取首行前 40 字。
    """
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    matches = list(_CHAPTER_RE.finditer(text))
    if not matches:
        first_line = text.split("\n", 1)[0].strip()[:40] or "正文"
        return [(first_line, text)]

    chapters: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip("\n")
        lines = block.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        chapters.append((title, body))
    return chapters


def count_words(text: str) -> int:
    return len((text or "").replace("\n", "").replace(" ", ""))