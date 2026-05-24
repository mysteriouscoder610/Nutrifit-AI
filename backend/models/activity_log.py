"""Activity log ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class ActivityLogType(str, enum.Enum):
    exercise = "exercise"
    walk = "walk"
    food_intake = "food_intake"
    custom = "custom"


class LoggedVia(str, enum.Enum):
    mcp = "mcp"
    manual = "manual"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    log_type = Column(Enum(ActivityLogType, name="activity_log_type"), nullable=False)
    description = Column(Text, nullable=False)
    value = Column(String(50), nullable=True)
    unit = Column(String(20), nullable=True)
    logged_via = Column(
        Enum(LoggedVia, name="logged_via"), default=LoggedVia.manual, nullable=False
    )
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="activity_logs")
