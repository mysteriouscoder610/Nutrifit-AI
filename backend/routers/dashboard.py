"""Dashboard summary + AI suggestions."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.activity_log import ActivityLog
from ..models.meal_log import MealLog
from ..models.user import User
from ..schemas.activity import ActivityLogOut
from ..schemas.dashboard import DashboardSummaryOut, SuggestionsOut, WeeklyNutrition
from ..schemas.meal import MealLogOut
from ..services import suggestion_service
from ..utils.auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardSummaryOut:
    since = datetime.utcnow() - timedelta(days=7)

    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == user.id)
        .order_by(MealLog.logged_at.desc())
        .limit(5)
        .all()
    )
    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.logged_at.desc())
        .limit(5)
        .all()
    )

    weekly_meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == user.id, MealLog.logged_at >= since)
        .all()
    )

    totals = WeeklyNutrition()
    by_day: dict = {}
    for m in weekly_meals:
        macros = m.macronutrients or {}
        cal = float(macros.get("calories_kcal", 0) or 0)
        prot = float(macros.get("protein_g", 0) or 0)
        carb = float(macros.get("carbohydrates_g", 0) or 0)
        fat = float(macros.get("fats_g", 0) or 0)
        totals.calories += cal
        totals.protein += prot
        totals.carbs += carb
        totals.fat += fat
        day = m.logged_at.strftime("%Y-%m-%d")
        bucket = by_day.setdefault(
            day, {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        )
        bucket["calories"] += cal
        bucket["protein"] += prot
        bucket["carbs"] += carb
        bucket["fat"] += fat

    days_sorted = sorted(by_day.keys())
    weekly_chart = {
        "labels": days_sorted,
        "calories": [by_day[d]["calories"] for d in days_sorted],
        "protein": [by_day[d]["protein"] for d in days_sorted],
        "carbs": [by_day[d]["carbs"] for d in days_sorted],
        "fat": [by_day[d]["fat"] for d in days_sorted],
    }

    return DashboardSummaryOut(
        name=user.name,
        recent_meals=[
            MealLogOut(
                id=m.id,
                image_url="/" + m.image_path.replace("\\", "/"),
                food_detected=m.food_detected,
                macronutrients=m.macronutrients,
                micronutrients=m.micronutrients,
                advice_good=m.advice_good,
                advice_bad=m.advice_bad,
                health_score=m.health_score,
                logged_at=m.logged_at,
            )
            for m in meals
        ],
        recent_activities=[ActivityLogOut.model_validate(a) for a in activities],
        weekly_nutrition=totals,
        weekly_chart=weekly_chart,
    )


@router.get("/suggestions", response_model=SuggestionsOut)
def suggestions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SuggestionsOut:
    try:
        result = suggestion_service.generate_suggestions(db, user.id, user.name, days=7)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM failed: {exc}") from exc
    return SuggestionsOut(**result)
