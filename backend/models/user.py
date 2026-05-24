"""User ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class UserRole(str, enum.Enum):
    user = "user"
    dietician = "dietician"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    username = Column(String(40), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    mobile_number = Column(String(15), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.user)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    dietician_profile = relationship(
        "DieticianProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatHistory", back_populates="user", cascade="all, delete-orphan"
    )
