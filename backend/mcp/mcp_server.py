"""
NutriFit AI — MCP Server
========================

This module exposes a Model Context Protocol (MCP) server that lets external AI
clients (Claude Desktop, Cursor, Gemini, etc.) log fitness/nutrition data
directly into NutriFit's PostgreSQL database via `activity_logs`.

It mirrors the 4 tools requested in the spec:
  • log_exercise(user_id, exercise_name, duration_minutes, intensity)
  • log_food_intake(user_id, food_description, quantity, unit)
  • log_walk(user_id, distance_km, duration_minutes)
  • log_custom_activity(user_id, description, value, unit)

Each call writes a row with `logged_via='mcp'`.

Reference implementation (TypeScript / Next.js):
  /Users/ayush.jha/major_project/fitness_coach_MCP/tools/

# ============================================================================
# USER WILL REPLACE THIS WITH THEIR OWN MCP TOOL CODE
# ----------------------------------------------------------------------------
# Drop your custom MCP framework / transport (mcp.server.fastmcp, raw stdio,
# SSE, etc.) inside the marked block below. The handlers `_log_*` already
# persist to NutriFit's database — your job is only to wire your transport's
# tool registration to call them.
# ============================================================================
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from ..database import SessionLocal
from ..models.activity_log import ActivityLog, ActivityLogType, LoggedVia
from ..models.user import User

logger = logging.getLogger("nutrifit.mcp")


# ---------------------------------------------------------------------------
# DB-writing handlers — these are the integration points the MCP transport
# layer should call. They are intentionally framework-agnostic so any MCP
# library (modelcontextprotocol/python-sdk, fastmcp, custom) can plug in.
# ---------------------------------------------------------------------------


def _resolve_user(db, user_id: str) -> User:
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    return user


def _persist(
    user_id: str,
    log_type: ActivityLogType,
    description: str,
    value: Optional[str] = None,
    unit: Optional[str] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        user = _resolve_user(db, user_id)
        log = ActivityLog(
            user_id=user.id,
            log_type=log_type,
            description=description,
            value=value,
            unit=unit,
            logged_via=LoggedVia.mcp,
            logged_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return {
            "ok": True,
            "id": str(log.id),
            "logged_at": log.logged_at.isoformat(),
            "type": log_type.value,
            "description": description,
        }
    except Exception as exc:
        db.rollback()
        logger.exception("MCP log failed: %s", exc)
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


def log_exercise(
    user_id: str,
    exercise_name: str,
    duration_minutes: float,
    intensity: str = "moderate",
) -> Dict[str, Any]:
    """Log an exercise session into NutriFit."""
    description = f"{exercise_name} ({intensity})"
    return _persist(
        user_id=user_id,
        log_type=ActivityLogType.exercise,
        description=description,
        value=str(duration_minutes),
        unit="minutes",
    )


def log_food_intake(
    user_id: str,
    food_description: str,
    quantity: float,
    unit: str,
) -> Dict[str, Any]:
    """Log a food/beverage intake into NutriFit."""
    return _persist(
        user_id=user_id,
        log_type=ActivityLogType.food_intake,
        description=food_description,
        value=str(quantity),
        unit=unit,
    )


def log_walk(
    user_id: str,
    distance_km: float,
    duration_minutes: float,
) -> Dict[str, Any]:
    """Log a walk into NutriFit."""
    description = f"Walk: {distance_km} km in {duration_minutes} min"
    return _persist(
        user_id=user_id,
        log_type=ActivityLogType.walk,
        description=description,
        value=str(distance_km),
        unit="km",
    )


def log_custom_activity(
    user_id: str,
    description: str,
    value: str,
    unit: str,
) -> Dict[str, Any]:
    """Log any custom activity (yoga, meditation, journaling, etc.) into NutriFit."""
    return _persist(
        user_id=user_id,
        log_type=ActivityLogType.custom,
        description=description,
        value=value,
        unit=unit,
    )


# ---------------------------------------------------------------------------
# Tool catalog — ready to be registered with any MCP framework.
# Each entry: (name, description, schema, handler)
# Mirrors the schema style from /major_project/fitness_coach_MCP/tools/.
# ---------------------------------------------------------------------------

TOOL_CATALOG = [
    {
        "name": "log_exercise",
        "description": "Log an exercise session (running, strength training, yoga, etc.) for a NutriFit user.",
        "schema": {
            "user_id": {"type": "string", "description": "NutriFit user UUID"},
            "exercise_name": {"type": "string", "description": "Name/type of the exercise"},
            "duration_minutes": {"type": "number", "description": "Duration in minutes"},
            "intensity": {
                "type": "string",
                "description": "low | moderate | high",
                "default": "moderate",
            },
        },
        "handler": log_exercise,
    },
    {
        "name": "log_food_intake",
        "description": "Log a food or beverage intake for a NutriFit user.",
        "schema": {
            "user_id": {"type": "string"},
            "food_description": {"type": "string"},
            "quantity": {"type": "number"},
            "unit": {"type": "string", "description": "g, ml, cup, slice, piece..."},
        },
        "handler": log_food_intake,
    },
    {
        "name": "log_walk",
        "description": "Log a walking session for a NutriFit user.",
        "schema": {
            "user_id": {"type": "string"},
            "distance_km": {"type": "number"},
            "duration_minutes": {"type": "number"},
        },
        "handler": log_walk,
    },
    {
        "name": "log_custom_activity",
        "description": "Log any custom activity (meditation, sleep, hydration, etc.) for a NutriFit user.",
        "schema": {
            "user_id": {"type": "string"},
            "description": {"type": "string"},
            "value": {"type": "string"},
            "unit": {"type": "string"},
        },
        "handler": log_custom_activity,
    },
]


# ============================================================================
# >>>  USER WILL REPLACE THIS WITH THEIR OWN MCP TOOL CODE  <<<
# ----------------------------------------------------------------------------
# Below is a minimal stdio runner using `mcp.server.fastmcp` if you have it
# installed.  Replace freely with your own server implementation. The handlers
# above are stable: just bind them to your tool definitions.
# ============================================================================


def run_stdio_server() -> None:  # pragma: no cover - integration entrypoint
    """Optional: run a FastMCP stdio server. Falls back to a print stub."""
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception:
        print("[NutriFit MCP] mcp SDK not installed. Replace with your transport.")
        for tool in TOOL_CATALOG:
            print(f"  • {tool['name']}: {tool['description']}")
        return

    server = FastMCP("nutrifit-ai")

    @server.tool()
    def log_exercise_tool(
        user_id: str,
        exercise_name: str,
        duration_minutes: float,
        intensity: str = "moderate",
    ) -> dict:
        """Log an exercise session into NutriFit."""
        return log_exercise(user_id, exercise_name, duration_minutes, intensity)

    @server.tool()
    def log_food_intake_tool(
        user_id: str,
        food_description: str,
        quantity: float,
        unit: str,
    ) -> dict:
        """Log a food / beverage intake into NutriFit."""
        return log_food_intake(user_id, food_description, quantity, unit)

    @server.tool()
    def log_walk_tool(
        user_id: str,
        distance_km: float,
        duration_minutes: float,
    ) -> dict:
        """Log a walk into NutriFit."""
        return log_walk(user_id, distance_km, duration_minutes)

    @server.tool()
    def log_custom_activity_tool(
        user_id: str,
        description: str,
        value: str,
        unit: str,
    ) -> dict:
        """Log a custom activity into NutriFit."""
        return log_custom_activity(user_id, description, value, unit)

    server.run()


if __name__ == "__main__":
    run_stdio_server()
