"""Chat history ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatSessionType(str, enum.Enum):
    rag = "rag"
    dashboard = "dashboard"
    consultation_qa = "consultation_qa"
    activity_qa = "activity_qa"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_type = Column(
        Enum(ChatSessionType, name="chat_session_type"), nullable=False
    )
    role = Column(Enum(ChatRole, name="chat_role"), nullable=False)
    message = Column(Text, nullable=False)
    reference_id = Column(String(80), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="chat_messages")
