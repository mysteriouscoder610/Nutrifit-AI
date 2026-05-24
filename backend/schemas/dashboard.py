"""Dashboard schemas."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel

from .activity import ActivityLogOut
from .meal import MealLogOut


class WeeklyNutrition(BaseModel):
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0


class DashboardSummaryOut(BaseModel):
    name: str
    recent_meals: List[MealLogOut]
    recent_activities: List[ActivityLogOut]
    weekly_nutrition: WeeklyNutrition
    weekly_chart: Dict[str, List[Any]]


class SuggestionsOut(BaseModel):
    diet_today: str
    workout_today: str
    insights: List[str]
