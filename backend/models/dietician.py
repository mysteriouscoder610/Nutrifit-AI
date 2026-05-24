"""Dietician profile ORM model."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class DieticianProfile(Base):
    __tablename__ = "dietician_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    speciality = Column(String(120), nullable=False)
    per_hour_charge = Column(Numeric(10, 2), nullable=False, default=0)
    per_two_hour_charge = Column(Numeric(10, 2), nullable=False, default=0)
    bio = Column(Text, nullable=True)
    location = Column(String(120), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="dietician_profile")
