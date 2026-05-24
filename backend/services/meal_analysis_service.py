"""Meal image -> structured nutrition analysis."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from . import gemini_service
from .prompts import MEAL_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


def _coerce_list(value: Any) -> list:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value]
    return []


def analyze_meal(image_path: Path) -> Dict[str, Any]:
    raw = gemini_service.analyze_image(MEAL_ANALYSIS_PROMPT, image_path)
    try:
        parsed = gemini_service.parse_json_response(raw)
    except Exception as exc:
        logger.exception("Failed to parse meal analysis JSON: %s", exc)
        parsed = {}

    food = _coerce_list(parsed.get("food_detected"))
    macros = parsed.get("macronutrients") or {}
    micros = parsed.get("micronutrients") or {}
    good = _coerce_list(parsed.get("advice_good"))
    bad = _coerce_list(parsed.get("advice_bad"))

    try:
        score = float(parsed.get("health_score", 0))
    except (TypeError, ValueError):
        score = 0.0

    return {
        "food_detected": food,
        "macronutrients": macros if isinstance(macros, dict) else {},
        "micronutrients": micros if isinstance(micros, dict) else {},
        "advice_good": good,
        "advice_bad": bad,
        "health_score": max(0.0, min(10.0, score)),
        "summary": str(parsed.get("summary", "")),
        "raw_response": raw,
    }
