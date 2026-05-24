"""Dietician listing + booking + consultation endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from ..config import ROOT_DIR, settings
from ..database import get_db
from ..models.consultation import Consultation, ConsultationStatus
from ..models.dietician import DieticianProfile
from ..models.user import User, UserRole
from ..schemas.consultation import (
    ConsultationAskIn,
    ConsultationCreateIn,
    ConsultationOut,
)
from ..schemas.dietician import DieticianCardOut, DieticianDetailOut
from ..services import gemini_service, transcription_service
from ..services.prompts import CONSULTATION_QA_PROMPT, CONSULTATION_SUMMARY_PROMPT
from ..utils.auth_utils import get_current_user
from ..utils.file_utils import ALLOWED_AUDIO_EXT, save_upload

router = APIRouter(prefix="/dieticians", tags=["dieticians"])
consultation_router = APIRouter(prefix="/consultations", tags=["consultations"])


def _card(user: User, profile: DieticianProfile) -> DieticianCardOut:
    return DieticianCardOut(
        id=user.id,
        name=user.name,
        speciality=profile.speciality,
        per_hour_charge=profile.per_hour_charge,
        per_two_hour_charge=profile.per_two_hour_charge,
        location=profile.location,
        bio=profile.bio,
        is_available=profile.is_available,
    )


@router.get("/", response_model=List[DieticianCardOut])
def list_dieticians(db: Session = Depends(get_db)) -> List[DieticianCardOut]:
    rows = (
        db.query(User)
        .options(joinedload(User.dietician_profile))
        .filter(User.role == UserRole.dietician)
        .all()
    )
    out: List[DieticianCardOut] = []
    for u in rows:
        if u.dietician_profile:
            out.append(_card(u, u.dietician_profile))
    return out


@router.get("/{dietician_id}", response_model=DieticianDetailOut)
def get_dietician(dietician_id: UUID, db: Session = Depends(get_db)) -> DieticianDetailOut:
    user = (
        db.query(User)
        .options(joinedload(User.dietician_profile))
        .filter(User.id == dietician_id, User.role == UserRole.dietician)
        .first()
    )
    if not user or not user.dietician_profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dietician not found")
    p = user.dietician_profile
    return DieticianDetailOut(
        id=user.id,
        name=user.name,
        speciality=p.speciality,
        per_hour_charge=p.per_hour_charge,
        per_two_hour_charge=p.per_two_hour_charge,
        location=p.location,
        bio=p.bio,
        is_available=p.is_available,
        email=user.email,
        mobile_number=user.mobile_number,
    )


@router.post("/book", response_model=ConsultationOut, status_code=status.HTTP_201_CREATED)
def book(
    payload: ConsultationCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultationOut:
    dietician = (
        db.query(User)
        .filter(User.id == payload.dietician_id, User.role == UserRole.dietician)
        .first()
    )
    if not dietician:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dietician not found")
    consultation = Consultation(
        user_id=user.id,
        dietician_id=dietician.id,
        scheduled_at=payload.scheduled_at or datetime.utcnow(),
        status=ConsultationStatus.scheduled,
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return ConsultationOut(
        id=consultation.id,
        user_id=consultation.user_id,
        dietician_id=consultation.dietician_id,
        dietician_name=dietician.name,
        scheduled_at=consultation.scheduled_at,
        status=consultation.status,
        has_recording=False,
    )


# ---------- consultation routes ----------


@consultation_router.get("/", response_model=List[ConsultationOut])
def list_consultations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[ConsultationOut]:
    if user.role == UserRole.dietician:
        rows = (
            db.query(Consultation)
            .filter(Consultation.dietician_id == user.id)
            .order_by(Consultation.scheduled_at.desc())
            .all()
        )
    else:
        rows = (
            db.query(Consultation)
            .filter(Consultation.user_id == user.id)
            .order_by(Consultation.scheduled_at.desc())
            .all()
        )
    out: List[ConsultationOut] = []
    for c in rows:
        dietician = db.query(User).filter(User.id == c.dietician_id).first()
        out.append(
            ConsultationOut(
                id=c.id,
                user_id=c.user_id,
                dietician_id=c.dietician_id,
                dietician_name=dietician.name if dietician else None,
                scheduled_at=c.scheduled_at,
                status=c.status,
                has_recording=bool(c.call_recording_path),
                transcript=c.transcript,
                llm_summary=c.llm_summary,
            )
        )
    return out


def _consultation_or_404(db: Session, consultation_id: UUID, user: User) -> Consultation:
    c = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultation not found")
    if user.id not in (c.user_id, c.dietician_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your consultation")
    return c


@consultation_router.post("/{consultation_id}/upload-recording", response_model=ConsultationOut)
async def upload_recording(
    consultation_id: UUID,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsultationOut:
    consultation = _consultation_or_404(db, consultation_id, user)
    saved = await save_upload(audio, settings.RECORDING_UPLOAD_DIR, ALLOWED_AUDIO_EXT)
    transcript = ""
    summary = ""
    try:
        transcript = transcription_service.transcribe(saved)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Transcription failed: {exc}") from exc
    if transcript.strip():
        try:
            summary = gemini_service.generate_text(
                CONSULTATION_SUMMARY_PROMPT.format(transcript=transcript),
                model=settings.GEMINI_FLASH_MODEL,
            )
        except Exception:
            summary = ""

    consultation.call_recording_path = str(saved.relative_to(ROOT_DIR))
    consultation.transcript = transcript
    consultation.llm_summary = summary
    consultation.status = ConsultationStatus.completed
    db.commit()
    db.refresh(consultation)

    dietician = db.query(User).filter(User.id == consultation.dietician_id).first()
    return ConsultationOut(
        id=consultation.id,
        user_id=consultation.user_id,
        dietician_id=consultation.dietician_id,
        dietician_name=dietician.name if dietician else None,
        scheduled_at=consultation.scheduled_at,
        status=consultation.status,
        has_recording=True,
        transcript=consultation.transcript,
        llm_summary=consultation.llm_summary,
    )


@consultation_router.post("/{consultation_id}/ask")
def ask_consultation(
    consultation_id: UUID,
    payload: ConsultationAskIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    consultation = _consultation_or_404(db, consultation_id, user)
    if not consultation.transcript:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No transcript available. Upload a recording first.",
        )
    prompt = CONSULTATION_QA_PROMPT.format(
        transcript=consultation.transcript,
        summary=consultation.llm_summary or "(none)",
        question=payload.question,
    )
    answer = gemini_service.generate_text(prompt, model=settings.GEMINI_FLASH_MODEL)
    return {"answer": answer}
