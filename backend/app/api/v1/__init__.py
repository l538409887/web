"""v1 路由汇总。"""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    author,
    books,
    categories,
    chapters,
    comments,
    home,
    authors,
    interaction,
    notices,
    rank,
    reports,
    shelf,
    upload,
    user,
    wallet,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(home.router)
api_router.include_router(auth.router)
api_router.include_router(books.router)
api_router.include_router(categories.router)
api_router.include_router(chapters.router)
api_router.include_router(comments.router)
api_router.include_router(shelf.router)
api_router.include_router(interaction.router)
api_router.include_router(rank.router)
api_router.include_router(notices.router)
api_router.include_router(authors.router)
api_router.include_router(reports.router)
api_router.include_router(upload.router)
api_router.include_router(user.router)
api_router.include_router(wallet.router)
api_router.include_router(author.router)
api_router.include_router(admin.router)