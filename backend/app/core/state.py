"""状态常量与可见性条件。

把「什么状态算对上架/可见」收敛到一处，避免各 service 里散落裸数字。
（历史上 audit_status=1 既表示"已通过"又被当作可见条件，
 改成四态后这类判断很容易漏改，所以统一到这里。）
"""
from sqlalchemy import and_

# ---------------- 书籍审核 ----------------
AUDIT_DRAFT = 0      # 草稿，未提交
AUDIT_PENDING = 1    # 已提交，待审核
AUDIT_APPROVED = 2   # 审核通过
AUDIT_REJECTED = 3   # 审核未通过

AUDIT_LABELS = {
    AUDIT_DRAFT: "未提交",
    AUDIT_PENDING: "待审核",
    AUDIT_APPROVED: "审核通过",
    AUDIT_REJECTED: "审核未通过",
}

# ---------------- 书籍上架 ----------------
SHELF_OFFLINE = 0    # 未上架
SHELF_PENDING = 1    # 上架申请中
SHELF_ONLINE = 2     # 已上架
SHELF_REJECTED = 3   # 上架申请被拒

SHELF_LABELS = {
    SHELF_OFFLINE: "未上架",
    SHELF_PENDING: "上架审核中",
    SHELF_ONLINE: "已上架",
    SHELF_REJECTED: "上架未通过",
}

# ---------------- 章节审核 ----------------
CHAPTER_DRAFT = 0
CHAPTER_PENDING = 1
CHAPTER_APPROVED = 2
CHAPTER_REJECTED = 3

CHAPTER_AUDIT_LABELS = {
    CHAPTER_DRAFT: "草稿",
    CHAPTER_PENDING: "待审核",
    CHAPTER_APPROVED: "已通过",
    CHAPTER_REJECTED: "未通过",
}

# ---------------- 间贴审核（先发后审）----------------
PC_PENDING = 0
PC_APPROVED = 1
PC_REJECTED = 2

PC_AUDIT_LABELS = {
    PC_PENDING: "待审核",
    PC_APPROVED: "已通过",
    PC_REJECTED: "已驳回",
}


def book_visible():
    """书籍在前台可见：审核通过 且 已上架。"""
    from app.models.book import Book

    return and_(Book.audit_status == AUDIT_APPROVED, Book.shelf_status == SHELF_ONLINE)


def chapter_visible():
    """章节在阅读端可见：未被隐藏 且 审核通过。"""
    from app.models.chapter import BookChapter

    return and_(BookChapter.status == 1, BookChapter.audit_status == CHAPTER_APPROVED)


def paragraph_visible():
    """间贴展示：未被隐藏 且 未被驳回（待审核的仍展示，先发后审）。"""
    from app.models.interaction import ParagraphComment

    return and_(
        ParagraphComment.status == 1, ParagraphComment.audit_status != PC_REJECTED
    )