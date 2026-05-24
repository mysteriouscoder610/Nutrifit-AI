"""Dietician-related response schemas."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DieticianCardOut(BaseModel):
    id: UUID
    name: str
    speciality: str
    per_hour_charge: Decimal
    per_two_hour_charge: Decimal
    location: Optional[str] = None
    bio: Optional[str] = None
    is_available: bool = True

    model_config = {"from_attributes": True}


class DieticianDetailOut(DieticianCardOut):
    email: str
    mobile_number: str
