"""Consultation schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.consultation import ConsultationStatus


class ConsultationCreateIn(BaseModel):
    dietician_id: UUID
    scheduled_at: Optional[datetime] = None


class ConsultationOut(BaseModel):
    id: UUID
    user_id: UUID
    dietician_id: UUID
    dietician_name: Optional[str] = None
    scheduled_at: datetime
    status: ConsultationStatus
    has_recording: bool = False
    transcript: Optional[str] = None
    llm_summary: Optional[str] = None


class ConsultationAskIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=600)
