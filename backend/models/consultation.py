"""Consultation ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class ConsultationStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dietician_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    call_recording_path = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    llm_summary = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(
        Enum(ConsultationStatus, name="consultation_status"),
        default=ConsultationStatus.scheduled,
        nullable=False,
    )

    user = relationship("User", foreign_keys=[user_id])
    dietician = relationship("User", foreign_keys=[dietician_id])
