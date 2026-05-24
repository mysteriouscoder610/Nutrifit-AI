"""RAG chat schemas."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RagChatIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    session_id: Optional[str] = None


class RagSource(BaseModel):
    title: str
    snippet: str


class RagChatOut(BaseModel):
    answer: str
    sources: List[RagSource] = []
