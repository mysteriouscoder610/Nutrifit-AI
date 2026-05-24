"""Filesystem helpers for uploaded media."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile, status

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"}
MAX_BYTES = 25 * 1024 * 1024  # 25 MB


def _ext(filename: str) -> str:
    return Path(filename).suffix.lower()


async def save_upload(
    upload: UploadFile,
    dest_dir: Path,
    allowed: Iterable[str],
) -> Path:
    if not upload or not upload.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No file uploaded")
    ext = _ext(upload.filename)
    if ext not in allowed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported file type: {ext}",
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / f"{uuid.uuid4().hex}{ext}"
    data = await upload.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File too large")
    target.write_bytes(data)
    return target


def public_url_for(absolute_path: Path, project_root: Path) -> str:
    try:
        rel = absolute_path.relative_to(project_root)
    except ValueError:
        rel = Path(absolute_path.name)
    return "/" + str(rel).replace("\\", "/")
