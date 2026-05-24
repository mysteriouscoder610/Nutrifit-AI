"""Thin wrapper around the Google Generative AI SDK."""
from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import google.generativeai as genai

from ..config import settings

logger = logging.getLogger(__name__)

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not configured; LLM calls will fail.")
        return
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _configured = True


def _model(model_name: Optional[str] = None) -> genai.GenerativeModel:
    _configure()
    return genai.GenerativeModel(model_name or settings.GEMINI_MODEL)


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse LLM JSON output, gracefully recovering from minor formatting issues."""
    cleaned = _strip_json_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            return json.loads(match.group(0))
        raise


def generate_text(prompt: str, *, model: Optional[str] = None, json_mode: bool = False) -> str:
    m = _model(model)
    config = {"response_mime_type": "application/json"} if json_mode else None
    response = m.generate_content(prompt, generation_config=config)
    return (response.text or "").strip()


def analyze_image(prompt: str, image_path: Path, *, model: Optional[str] = None) -> str:
    m = _model(model)
    image_bytes = image_path.read_bytes()
    mime = "image/jpeg"
    suffix = image_path.suffix.lower()
    if suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"
    elif suffix == ".gif":
        mime = "image/gif"
    response = m.generate_content([
        prompt,
        {"mime_type": mime, "data": image_bytes},
    ])
    return (response.text or "").strip()


def transcribe_audio(audio_path: Path) -> str:
    """Transcribe audio with Gemini's audio understanding capability."""
    m = _model(settings.GEMINI_MODEL)
    audio_bytes = audio_path.read_bytes()
    suffix = audio_path.suffix.lower().lstrip(".")
    mime_map = {
        "mp3": "audio/mp3",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "webm": "audio/webm",
        "flac": "audio/flac",
    }
    mime = mime_map.get(suffix, "audio/mpeg")
    instruction = (
        "Transcribe this audio verbatim. Output only the transcript text, "
        "no speaker labels unless they are clear, no commentary."
    )
    response = m.generate_content([
        instruction,
        {"mime_type": mime, "data": audio_bytes},
    ])
    return (response.text or "").strip()
