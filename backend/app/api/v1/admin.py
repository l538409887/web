"""管理后台接口（整个路由要求 admin 角色）。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from loguru import logger
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.response import ok
from app.models.user import SysUser
from app.schemas.wallet import AdminOrderItem
from app.schemas.admin import (
    AdminBookItem,
    AdminCommentItem,
    AdminUserItem,
    BookCreateIn,
    BookStatusIn,
    CategoryIn,
    ChapterImportIn,
    CommentStatusIn,
    StatsOut,
    UserUpdateIn,
)
from app.schemas.common import PageResult
from app.services import admin_service, wallet_service, author_service

router = APIRouter(
    prefix="/admin",
    tags=["管理后台"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("/stats", summary="数据看板")
def get_stats(db: Session = Depends(get_db)):
    return ok(StatsOut(**admin_service.get_stats(db)))


# ---------------- 书籍 ----------------
@router.get("/books", summary="书籍管理列表")
def list_books(
    keyword: str | None = None,
    audit_status: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = admin_service.list_books(
        db, keyword=keyword, audit_status=audit_status, page=page, size=size
    )
    items = [AdminBookItem.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[AdminBookItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.post("/books", summary="新建书籍")
def create_book(payload: BookCreateIn, db: Session = Depends(get_db)):
    book = admin_service.create_book(db, payload)
    logger.bind(business=True).info("BOOK_CREATE book={} title={}", book.id, book.title)
    return ok({"id": book.id, "title": book.title})


@router.put("/books/{book_id}/status", summary="上下架 / 推荐位")
def update_book_status(
    book_id: int, payload: BookStatusIn, db: Session = Depends(get_db)
):
    admin_service.update_book_status(
        db, book_id, payload.audit_status, payload.is_recommend, payload.shelf_status
    )
    logger.bind(business=True).info(
        "BOOK_AUDIT book={} audit={} recommend={}",
        book_id,
        payload.audit_status,
        payload.is_recommend,
    )
    return ok({"book_id": book_id})


@router.post("/books/{book_id}/chapters/preview", summary="分章预览（不落库）")
def preview_chapters(book_id: int, payload: ChapterImportIn, db: Session = Depends(get_db)):
    items = admin_service.preview_chapters(db, book_id, payload.raw_text)
    return ok({"count": len(items), "items": items})


@router.post("/books/{book_id}/chapters/import", summary="粘贴文本自动分章导入")
def import_chapters(
    book_id: int, payload: ChapterImportIn, db: Session = Depends(get_db)
):
    result = admin_service.import_chapters(db, book_id, payload.raw_text)
    logger.bind(business=True).info(
        "CHAPTER_IMPORT book={} imported={}", book_id, result["imported"]
    )
    return ok(result)


# ---------------- 用户 ----------------
@router.get("/users", summary="用户列表")
def list_users(
    keyword: str | None = None,
    role: str | None = None,
    status: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = admin_service.list_users(
        db, keyword=keyword, role=role, status=status, page=page, size=size
    )
    items = [AdminUserItem.model_validate(row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[AdminUserItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.put("/users/{user_id}", summary="禁用 / 启用 / 改角色")
def update_user(
    user_id: int,
    payload: UserUpdateIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    admin_service.update_user(db, admin, user_id, payload.status, payload.role)
    logger.bind(business=True).info(
        "USER_STATUS_CHANGE admin={} target={} status={} role={}",
        admin.id,
        user_id,
        payload.status,
        payload.role,
    )
    return ok({"user_id": user_id})


# ---------------- 评论 ----------------
@router.get("/comments", summary="评论管理列表")
def list_comments(
    book_id: int | None = None,
    status: int | None = None,
    reported: bool = False,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = admin_service.list_comments(
        db, book_id=book_id, status=status, page=page, size=size, reported=reported
    )
    items = [AdminCommentItem(**row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[AdminCommentItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.put("/comments/{comment_id}/status", summary="隐藏 / 恢复评论")
def update_comment_status(
    comment_id: int, payload: CommentStatusIn, db: Session = Depends(get_db)
):
    admin_service.update_comment_status(db, comment_id, payload.status)
    return ok({"comment_id": comment_id, "status": payload.status})


# ---------------- 分类 ----------------
@router.post("/categories", summary="新增分类")
def create_category(payload: CategoryIn, db: Session = Depends(get_db)):
    category = admin_service.create_category(db, payload.name, payload.sort)
    return ok({"id": category.id, "name": category.name, "sort": category.sort})


@router.put("/categories/{category_id}", summary="修改分类")
def update_category(
    category_id: int, payload: CategoryIn, db: Session = Depends(get_db)
):
    admin_service.update_category(db, category_id, payload.name, payload.sort)
    return ok({"category_id": category_id})


@router.delete("/categories/{category_id}", summary="删除分类")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    admin_service.delete_category(db, category_id)
    return ok(None)

# ---------------- 充值订单 ----------------
@router.get("/orders", summary="充值订单列表")
def list_orders(
    status: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = wallet_service.list_orders(db, status, page, size)
    items = [AdminOrderItem(**row) for row in rows]
    pages = (total + size - 1) // size
    return ok(
        PageResult[AdminOrderItem](
            list=items, total=total, page=page, size=size, pages=pages
        )
    )


@router.put("/orders/{order_id}/confirm", summary="确认到账")
def confirm_order(
    order_id: int,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = wallet_service.confirm_order(db, admin.id, order_id)
    logger.bind(business=True).info(
        "ORDER_CONFIRM admin={} order={} coin={}", admin.id, order_id, result["coin_added"]
    )
    return ok(result)


@router.put("/orders/{order_id}/cancel", summary="取消订单")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    wallet_service.cancel_order(db, order_id)
    return ok(None)

# ---------------- 间贴审核 ----------------
@router.get("/paragraph-comments", summary="间贴列表（可按举报筛选）")
def list_paragraph_comments(
    status: int | None = None,
    only_reported: bool = False,
    audit_status: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    from app.services import interaction_service

    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = interaction_service.admin_list_paragraph_comments(
        db,
        status=status,
        only_reported=only_reported,
        audit_status=audit_status,
        page=page,
        size=size,
    )
    pages = (total + size - 1) // size
    return ok(
        {
            "list": rows,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }
    )


@router.put("/paragraph-comments/{comment_id}/status", summary="隐藏 / 恢复间贴")
def update_paragraph_status(
    comment_id: int,
    payload: CommentStatusIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import interaction_service

    interaction_service.set_paragraph_status(db, comment_id, payload.status)
    logger.bind(business=True).info(
        "PARAGRAPH_MODERATE admin={} comment={} status={}",
        admin.id,
        comment_id,
        payload.status,
    )
    return ok({"comment_id": comment_id, "status": payload.status})

# ---------------- 公告管理 ----------------
class NoticeIn(BaseModel):
    title: str
    content: str = ""
    category: str = "公告"
    is_top: bool = False


class NoticePatch(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    is_top: bool | None = None
    status: bool | None = None


@router.get("/notices", summary="公告列表")
def admin_list_notices(
    status: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    from app.services import notice_service

    page = max(1, page)
    size = min(max(1, size), 50)
    rows, total = notice_service.list_all(db, status, page, size)
    pages = (total + size - 1) // size
    return ok(
        {
            "list": [
                {
                    "id": r.id,
                    "title": r.title,
                    "content": r.content,
                    "category": r.category,
                    "is_top": bool(r.is_top),
                    "status": r.status,
                    "created_at": r.created_at,
                }
                for r in rows
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }
    )


@router.post("/notices", summary="新建公告")
def admin_create_notice(
    payload: NoticeIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import notice_service

    row = notice_service.create(db, payload.title, payload.content, payload.category, payload.is_top)
    logger.bind(business=True).info("NOTICE_CREATE admin={} id={}", admin.id, row.id)
    return ok({"id": row.id})


@router.put("/notices/{notice_id}", summary="修改公告")
def admin_update_notice(
    notice_id: int,
    payload: NoticePatch,
    db: Session = Depends(get_db),
):
    from app.services import notice_service

    row = notice_service.update(db, notice_id, payload.model_dump(exclude_unset=True))
    return ok({"id": row.id, "status": row.status})


@router.delete("/notices/{notice_id}", summary="删除公告")
def admin_delete_notice(notice_id: int, db: Session = Depends(get_db)):
    from app.services import notice_service

    notice_service.delete(db, notice_id)
    return ok(None)

# ---------------- 举报处理 ----------------
class ReportActionIn(BaseModel):
    action: str


@router.get("/reports", summary="举报队列")
def admin_list_reports(
    status: int | None = 0,
    target_type: str | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    from app.services import report_service

    page = max(1, page)
    size = min(max(1, size), 50)
    items, total = report_service.list_reports(
        db, status=status, target_type=target_type, page=page, size=size
    )
    pages = (total + size - 1) // size
    return ok(
        {"list": items, "total": total, "page": page, "size": size, "pages": pages}
    )


@router.put("/reports/{report_id}", summary="处理举报")
def admin_handle_report(
    report_id: int,
    payload: ReportActionIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import report_service

    result = report_service.handle_report(db, admin.id, report_id, payload.action)
    logger.bind(business=True).info(
        "REPORT_HANDLE admin={} report={} action={}",
        admin.id,
        report_id,
        payload.action,
    )
    return ok(result)


# ---------------- 章节审核 ----------------
class ChapterAuditIn(BaseModel):
    audit_status: int


@router.get("/chapters", summary="章节审核队列")
def admin_list_chapters(
    audit_status: int | None = 1,
    book_id: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = min(max(1, size), 50)
    items, total = admin_service.list_chapters_for_audit(
        db, audit_status=audit_status, book_id=book_id, page=page, size=size
    )
    pages = (total + size - 1) // size
    return ok({"list": items, "total": total, "page": page, "size": size, "pages": pages})


@router.put("/chapters/{chapter_id}/audit", summary="审核章节")
def admin_audit_chapter(
    chapter_id: int,
    payload: ChapterAuditIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    admin_service.update_chapter_audit(db, chapter_id, payload.audit_status)
    logger.bind(business=True).info(
        "CHAPTER_AUDIT admin={} chapter={} status={}",
        admin.id,
        chapter_id,
        payload.audit_status,
    )
    return ok({"chapter_id": chapter_id, "audit_status": payload.audit_status})


# ---------------- 间贴审核 ----------------
class ParagraphAuditIn(BaseModel):
    audit_status: int


@router.put("/paragraph-comments/{comment_id}/audit", summary="审核间贴")
def admin_audit_paragraph(
    comment_id: int,
    payload: ParagraphAuditIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import interaction_service

    interaction_service.set_paragraph_audit(db, comment_id, payload.audit_status)
    logger.bind(business=True).info(
        "PARAGRAPH_AUDIT admin={} comment={} status={}",
        admin.id,
        comment_id,
        payload.audit_status,
    )
    return ok({"comment_id": comment_id, "audit_status": payload.audit_status})


# ---------------- 敏感词库 ----------------
class WordIn(BaseModel):
    word: str
    level: str = "review"
    category: str = "其他"


class WordPatch(BaseModel):
    level: str | None = None
    category: str | None = None
    is_active: bool | None = None


class WordTestIn(BaseModel):
    text: str


@router.get("/sensitive-words", summary="敏感词列表")
def admin_list_words(
    keyword: str | None = None,
    level: str | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    from app.services import moderation_service

    page = max(1, page)
    size = min(max(1, size), 100)
    rows, total = moderation_service.list_words(db, keyword, level, page, size)
    pages = (total + size - 1) // size
    return ok(
        {
            "list": [
                {
                    "id": r.id,
                    "word": r.word,
                    "level": r.level,
                    "category": r.category,
                    "is_active": bool(r.is_active),
                    "created_at": r.created_at,
                }
                for r in rows
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }
    )


@router.post("/sensitive-words", summary="新增敏感词")
def admin_create_word(
    payload: WordIn,
    admin: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services import moderation_service

    row = moderation_service.create_word(db, payload.word, payload.level, payload.category)
    logger.bind(business=True).info("WORD_CREATE admin={} word={}", admin.id, row.id)
    return ok({"id": row.id})


@router.put("/sensitive-words/{word_id}", summary="修改敏感词")
def admin_update_word(
    word_id: int,
    payload: WordPatch,
    db: Session = Depends(get_db),
):
    from app.services import moderation_service

    row = moderation_service.update_word(
        db, word_id, **payload.model_dump(exclude_unset=True)
    )
    return ok({"id": row.id, "is_active": bool(row.is_active)})


@router.delete("/sensitive-words/{word_id}", summary="删除敏感词")
def admin_delete_word(word_id: int, db: Session = Depends(get_db)):
    from app.services import moderation_service

    moderation_service.delete_word(db, word_id)
    return ok(None)


@router.post("/sensitive-words/test", summary="检测一段文本")
def admin_test_words(payload: WordTestIn, db: Session = Depends(get_db)):
    from app.services import moderation_service

    result = moderation_service.scan(db, payload.text)
    return ok(
        {
            "blocked": result["blocked"],
            "review": result["review"],
            "would_block": bool(result["blocked"]),
        }
    )