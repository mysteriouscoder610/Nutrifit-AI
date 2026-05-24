"""RAG chat endpoints (text and image)."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.chat_history import ChatHistory, ChatRole, ChatSessionType
from ..models.user import User
from ..schemas.rag import RagChatIn, RagChatOut, RagSource
from ..services import gemini_service, rag_service
from ..services.prompts import DISEASE_IMAGE_PROMPT
from ..utils.auth_utils import get_current_user
from ..utils.file_utils import ALLOWED_IMAGE_EXT, save_upload

router = APIRouter(prefix="/rag", tags=["rag"])


def _persist(db: Session, user_id, role: ChatRole, message: str) -> None:
    db.add(
        ChatHistory(
            user_id=user_id,
            session_type=ChatSessionType.rag,
            role=role,
            message=message,
        )
    )


@router.post("/chat", response_model=RagChatOut)
def chat(
    payload: RagChatIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RagChatOut:
    try:
        result = rag_service.answer_with_rag(payload.question)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"RAG failed: {exc}") from exc

    _persist(db, user.id, ChatRole.user, payload.question)
    _persist(db, user.id, ChatRole.assistant, result["answer"])
    db.commit()
    return RagChatOut(
        answer=result["answer"],
        sources=[RagSource(**s) for s in result["sources"]],
    )


@router.post("/chat-with-image", response_model=RagChatOut)
async def chat_with_image(
    question: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RagChatOut:
    saved = await save_upload(image, settings.DISEASE_UPLOAD_DIR, ALLOWED_IMAGE_EXT)
    try:
        raw = gemini_service.analyze_image(DISEASE_IMAGE_PROMPT, saved)
        parsed = gemini_service.parse_json_response(raw)
    except Exception:
        parsed = {"condition": "unidentified", "context": ""}

    condition = str(parsed.get("condition", "")).strip() or "unidentified"
    context_hint = str(parsed.get("context", "")).strip()

    effective_q = (
        question.strip()
        or f"Provide dietary and lifestyle guidance for someone with {condition}."
    )

    try:
        result = rag_service.answer_with_rag(effective_q, context_hint=context_hint)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"RAG failed: {exc}") from exc

    user_msg = f"[image: {condition}] {effective_q}"
    _persist(db, user.id, ChatRole.user, user_msg)
    _persist(db, user.id, ChatRole.assistant, result["answer"])
    db.commit()
    return RagChatOut(
        answer=result["answer"],
        sources=[RagSource(**s) for s in result["sources"]],
    )


@router.get("/history")
def history(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list:
    rows = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == user.id,
            ChatHistory.session_type == ChatSessionType.rag,
        )
        .order_by(ChatHistory.created_at.asc())
        .limit(min(limit, 200))
        .all()
    )
    return [
        {"role": r.role.value, "message": r.message, "created_at": r.created_at.isoformat()}
        for r in rows
    ]
