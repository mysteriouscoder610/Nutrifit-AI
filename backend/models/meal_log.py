"""Meal log ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..database import Base


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_path = Column(String(500), nullable=False)
    food_detected = Column(Text, nullable=True)
    macronutrients = Column(JSONB, nullable=True)
    micronutrients = Column(JSONB, nullable=True)
    advice_good = Column(Text, nullable=True)
    advice_bad = Column(Text, nullable=True)
    health_score = Column(String(8), nullable=True)
    raw_llm_response = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="meal_logs")
