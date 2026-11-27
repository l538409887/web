"""文件上传接口（封面 / 头像）。"""
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from loguru import logger

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.exceptions import BizError
from app.core.response import ok
from app.models.user import SysUser

router = APIRouter(tags=["上传"])

ALLOWED = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAGIC = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"RIFF": ".webp",
}

SCENE_DIR = {"cover": "covers", "avatar": "avatars"}


def _sniff_ext(data: bytes) -> str | None:
    for magic, ext in MAGIC.items():
        if data.startswith(magic):
            return ext
    return None


@router.post("/upload", summary="上传图片（封面 / 头像）")
async def upload_image(
    file: UploadFile = File(...),
    scene: str = Form("cover"),
    user: SysUser = Depends(get_current_user),
):
    if scene not in SCENE_DIR:
        raise BizError(1001, "scene 只能是 cover 或 avatar")

    data = await file.read()
    if not data:
        raise BizError(1001, "文件为空")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise BizError(1001, f"图片不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB")

    ext = _sniff_ext(data)
    if ext is None:
        raise BizError(1001, "只支持 jpg / png / webp 图片")

    day = datetime.now().strftime("%Y%m%d")
    sub = SCENE_DIR[scene]
    target_dir = Path(settings.STATIC_DIR) / sub / day
    target_dir.mkdir(parents=True, exist_ok=True)

    name = f"{uuid.uuid4().hex}{ext}"
    (target_dir / name).write_bytes(data)

    url = f"/static/{sub}/{day}/{name}"
    logger.bind(business=True).info(
        "UPLOAD user={} scene={} bytes={} url={}", user.id, scene, len(data), url
    )
    return ok({"url": url, "size": len(data)})