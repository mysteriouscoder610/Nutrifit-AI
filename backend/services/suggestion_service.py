"""Daily AI-generated diet/workout suggestions and natural-language Q&A on logs."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..config import settings
from ..models.activity_log import ActivityLog
from ..models.meal_log import MealLog
from . import gemini_service
from .prompts import ACTIVITY_QA_PROMPT, SUGGESTIONS_PROMPT

logger = logging.getLogger(__name__)


def _activities_for(db: Session, user_id, since: datetime) -> List[ActivityLog]:
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id, ActivityLog.logged_at >= since)
        .order_by(ActivityLog.logged_at.desc())
        .all()
    )


def _meals_for(db: Session, user_id, since: datetime) -> List[MealLog]:
    return (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id, MealLog.logged_at >= since)
        .order_by(MealLog.logged_at.desc())
        .all()
    )


def _format_activities(items: List[ActivityLog]) -> str:
    if not items:
        return "(no activity logged)"
    return "\n".join(
        f"- {a.logged_at:%Y-%m-%d %H:%M} | {a.log_type.value} | {a.description} "
        f"({a.value or '-'} {a.unit or ''})"
        for a in items
    )


def _format_meals(items: List[MealLog]) -> str:
    if not items:
        return "(no meals logged)"
    rows = []
    for m in items:
        macros = m.macronutrients or {}
        cal = macros.get("calories_kcal", "?")
        prot = macros.get("protein_g", "?")
        rows.append(
            f"- {m.logged_at:%Y-%m-%d %H:%M} | {m.food_detected or 'meal'} "
            f"| cal={cal} prot={prot}g"
        )
    return "\n".join(rows)


def generate_suggestions(db: Session, user_id, name: str, days: int = 7) -> Dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=days)
    activities = _activities_for(db, user_id, since)
    meals = _meals_for(db, user_id, since)
    prompt = SUGGESTIONS_PROMPT.format(
        name=name,
        days=days,
        activities=_format_activities(activities),
        meals=_format_meals(meals),
    )
    try:
        text = gemini_service.generate_text(
            prompt, model=settings.GEMINI_FLASH_MODEL, json_mode=True
        )
        parsed = gemini_service.parse_json_response(text)
    except Exception as exc:
        logger.exception("Suggestion generation failed: %s", exc)
        return {
            "diet_today": "Start with a balanced breakfast (eggs + oats), a vegetable-heavy lunch, a fruit snack, and a lean-protein dinner. Hydrate well.",
            "workout_today": "30 minutes brisk walk + 10 minutes mobility. Add a light bodyweight circuit if you have energy.",
            "insights": ["Log a few meals and activities so I can tailor this to you."],
        }
    return {
        "diet_today": str(parsed.get("diet_today", "")),
        "workout_today": str(parsed.get("workout_today", "")),
        "insights": [str(x) for x in (parsed.get("insights") or [])],
    }


def answer_log_question(db: Session, user_id, question: str, days: int = 7) -> str:
    since = datetime.utcnow() - timedelta(days=days)
    activities = _activities_for(db, user_id, since)
    meals = _meals_for(db, user_id, since)
    prompt = ACTIVITY_QA_PROMPT.format(
        question=question,
        days=days,
        activities=_format_activities(activities),
        meals=_format_meals(meals),
    )
    return gemini_service.generate_text(prompt, model=settings.GEMINI_FLASH_MODEL)
