"""Meal analysis schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class MealAnalysisOut(BaseModel):
    id: UUID
    image_url: str
    food_detected: List[str]
    macronutrients: Dict[str, Any]
    micronutrients: Dict[str, Any]
    advice_good: List[str]
    advice_bad: List[str]
    health_score: float
    raw_response: Optional[str] = None
    logged_at: datetime


class MealLogOut(BaseModel):
    id: UUID
    image_url: str
    food_detected: Optional[str] = None
    macronutrients: Optional[Dict[str, Any]] = None
    micronutrients: Optional[Dict[str, Any]] = None
    advice_good: Optional[str] = None
    advice_bad: Optional[str] = None
    health_score: Optional[str] = None
    logged_at: datetime

    model_config = {"from_attributes": True}
