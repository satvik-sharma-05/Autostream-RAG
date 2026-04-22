"""LangGraph tools for the AutoStream agent."""
import os
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

from app.utils.validators import is_valid_email, sanitize_name
from app.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory lead store (replace with DB in production)
_captured_leads: list = []


@tool
def capture_lead(name: str, email: str, platform: str) -> str:
    """
    Capture a qualified lead after collecting all required information.

    Args:
        name: Full name of the prospect
        email: Email address (must be valid)
        platform: Social media platform (YouTube, TikTok, Instagram, etc.)

    Returns:
        Success or error message
    """
    if not is_valid_email(email):
        return f"Invalid email address: {email}. Please ask the user to provide a valid email."

    clean_name = sanitize_name(name)
    lead = {
        "name": clean_name,
        "email": email.strip().lower(),
        "platform": platform.strip(),
        "captured_at": datetime.utcnow().isoformat(),
        "status": "new",
    }
    _captured_leads.append(lead)
    logger.info(f"Lead captured: {lead}")
    return (
        f"Lead successfully captured! "
        f"Name: {clean_name}, Email: {email}, Platform: {platform}. "
        f"Our team will reach out within 24 hours."
    )


def get_all_leads() -> list:
    """Return all captured leads (for API endpoint)."""
    return _captured_leads
