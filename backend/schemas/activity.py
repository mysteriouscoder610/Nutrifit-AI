"""Activity log schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.activity_log import ActivityLogType, LoggedVia


class ActivityLogIn(BaseModel):
    log_type: ActivityLogType
    description: str = Field(..., min_length=1, max_length=500)
    value: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)


class ActivityLogOut(BaseModel):
    id: UUID
    log_type: ActivityLogType
    description: str
    value: Optional[str] = None
    unit: Optional[str] = None
    logged_via: LoggedVia
    logged_at: datetime

    model_config = {"from_attributes": True}


class ActivityAskIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=600)
    window_days: int = Field(7, ge=1, le=90)
