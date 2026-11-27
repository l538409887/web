"""正文水印：把用户 ID 编成零宽字符嵌进正文。

用途是**溯源**而不是阻止复制：
已购买用户拿到的正文里藏着只属于他的标识，一旦内容外流，
可以从截图/抓取的文本里解出是谁泄露的。

零宽字符在浏览器里不可见、不影响排版，但会被文本复制带走。
"""
ZERO = "\u200b"  # U+200B ZERO WIDTH SPACE，表示二进制 0
ONE = "\u200c"   # U+200C ZERO WIDTH NON-JOINER，表示二进制 1
SEP = "\u200d"   # U+200D ZERO WIDTH JOINER，作为分隔符

# 每隔多少段插入一次水印（降低被整体删除后无法溯源的概率）
EVERY_N_PARAGRAPHS = 3


def encode(user_id: int) -> str:
    if not user_id:
        return ""
    bits = format(int(user_id), "b")
    return SEP + "".join(ONE if b == "1" else ZERO for b in bits) + SEP


def decode(mark: str) -> int:
    """从一段水印里还原用户 ID（供排查工具使用）。"""
    raw = mark.strip(SEP)
    if not raw:
        return 0
    bits = "".join("1" if ch == ONE else "0" for ch in raw if ch in (ZERO, ONE))
    try:
        return int(bits, 2)
    except ValueError:
        return 0


def embed(text: str, user_id: int) -> str:
    """按段落间隔插入水印；正文很短时只加在末尾。"""
    if not text or not user_id:
        return text

    mark = encode(user_id)
    lines = text.split("\n")
    out = list(lines)

    # 追加到行尾而不是插入新行：这样 strip() 后能原样还原，
    # 正文段落数也不会因为水印而变化。
    for index in range(len(out)):
        if (index + 1) % EVERY_N_PARAGRAPHS == 0:
            out[index] = out[index] + mark

    if out:
        out[-1] = out[-1] + mark
    return "\n".join(out)


def strip(text: str) -> str:
    """去掉正文里的全部零宽字符（导出/比对时用）。"""
    return "".join(ch for ch in (text or "") if ch not in (ZERO, ONE, SEP))
