"""Pydantic schemas for chat endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    intent_confidence: float
    lead_captured: bool
    turn_count: int
