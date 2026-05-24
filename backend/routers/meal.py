"""Meal image analysis endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..config import ROOT_DIR, settings
from ..database import get_db
from ..models.meal_log import MealLog
from ..models.user import User
from ..schemas.meal import MealAnalysisOut, MealLogOut
from ..services import meal_analysis_service
from ..utils.auth_utils import get_current_user
from ..utils.file_utils import ALLOWED_IMAGE_EXT, public_url_for, save_upload

router = APIRouter(prefix="/meal", tags=["meal"])


@router.post("/analyze", response_model=MealAnalysisOut)
async def analyze_meal(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealAnalysisOut:
    saved_path = await save_upload(image, settings.MEAL_UPLOAD_DIR, ALLOWED_IMAGE_EXT)
    try:
        result = meal_analysis_service.analyze_meal(saved_path)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Meal analysis failed: {exc}"
        ) from exc

    log = MealLog(
        user_id=user.id,
        image_path=str(saved_path.relative_to(ROOT_DIR)),
        food_detected=", ".join(result["food_detected"]),
        macronutrients=result["macronutrients"],
        micronutrients=result["micronutrients"],
        advice_good="\n".join(result["advice_good"]),
        advice_bad="\n".join(result["advice_bad"]),
        health_score=str(result["health_score"]),
        raw_llm_response=result["raw_response"],
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return MealAnalysisOut(
        id=log.id,
        image_url=public_url_for(saved_path, ROOT_DIR),
        food_detected=result["food_detected"],
        macronutrients=result["macronutrients"],
        micronutrients=result["micronutrients"],
        advice_good=result["advice_good"],
        advice_bad=result["advice_bad"],
        health_score=result["health_score"],
        raw_response=result["summary"],
        logged_at=log.logged_at,
    )


@router.get("/history", response_model=List[MealLogOut])
def history(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[MealLogOut]:
    logs = (
        db.query(MealLog)
        .filter(MealLog.user_id == user.id)
        .order_by(MealLog.logged_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        MealLogOut(
            id=log.id,
            image_url="/" + log.image_path.replace("\\", "/"),
            food_detected=log.food_detected,
            macronutrients=log.macronutrients,
            micronutrients=log.micronutrients,
            advice_good=log.advice_good,
            advice_bad=log.advice_bad,
            health_score=log.health_score,
            logged_at=log.logged_at,
        )
        for log in logs
    ]
