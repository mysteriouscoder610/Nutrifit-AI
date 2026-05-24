"""Audio -> transcript wrapper. Uses Gemini by default, optional Whisper fallback."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import gemini_service

logger = logging.getLogger(__name__)


def transcribe(audio_path: Path) -> str:
    backend = os.getenv("TRANSCRIPTION_BACKEND", "gemini").lower()
    if backend == "whisper":
        try:
            import whisper  # type: ignore

            model_name = os.getenv("WHISPER_MODEL", "base")
            model = whisper.load_model(model_name)
            result = model.transcribe(str(audio_path))
            return (result.get("text") or "").strip()
        except Exception as exc:
            logger.exception("Whisper transcription failed, falling back to Gemini: %s", exc)
    return gemini_service.transcribe_audio(audio_path)
