"""Activity logging + Q&A endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.activity_log import ActivityLog, LoggedVia
from ..models.chat_history import ChatHistory, ChatRole, ChatSessionType
from ..models.user import User
from ..schemas.activity import ActivityAskIn, ActivityLogIn, ActivityLogOut
from ..services import suggestion_service
from ..utils.auth_utils import get_current_user

router = APIRouter(prefix="/activity", tags=["activity"])


@router.post("/log", response_model=ActivityLogOut)
def log_activity(
    payload: ActivityLogIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ActivityLogOut:
    log = ActivityLog(
        user_id=user.id,
        log_type=payload.log_type,
        description=payload.description,
        value=payload.value,
        unit=payload.unit,
        logged_via=LoggedVia.manual,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return ActivityLogOut.model_validate(log)


@router.get("/history", response_model=List[ActivityLogOut])
def history(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[ActivityLogOut]:
    rows = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.logged_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return [ActivityLogOut.model_validate(r) for r in rows]


@router.post("/ask")
def ask_about_logs(
    payload: ActivityAskIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        answer = suggestion_service.answer_log_question(
            db, user.id, payload.question, days=payload.window_days
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM failed: {exc}") from exc

    db.add_all([
        ChatHistory(
            user_id=user.id,
            session_type=ChatSessionType.activity_qa,
            role=ChatRole.user,
            message=payload.question,
        ),
        ChatHistory(
            user_id=user.id,
            session_type=ChatSessionType.activity_qa,
            role=ChatRole.assistant,
            message=answer,
        ),
    ])
    db.commit()
    return {"answer": answer}
