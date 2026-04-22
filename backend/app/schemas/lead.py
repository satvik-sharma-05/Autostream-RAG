"""Pydantic schemas for lead endpoints."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeadResponse(BaseModel):
    name: str
    email: str
    platform: str
    captured_at: str
    status: str
