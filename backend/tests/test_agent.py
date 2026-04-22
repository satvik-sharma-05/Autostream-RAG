"""Unit tests for lead capture tool."""
import pytest
from app.core.tools import capture_lead, get_all_leads


def test_capture_lead_valid():
    result = capture_lead.invoke({"name": "Jane Doe", "email": "jane@example.com", "platform": "YouTube"})
    assert "successfully captured" in result.lower()
    leads = get_all_leads()
    assert any(l["email"] == "jane@example.com" for l in leads)


def test_capture_lead_invalid_email():
    result = capture_lead.invoke({"name": "Bad User", "email": "not-an-email", "platform": "TikTok"})
    assert "invalid email" in result.lower()


def test_capture_lead_name_sanitized():
    capture_lead.invoke({"name": "  john smith  ", "email": "john@test.com", "platform": "Instagram"})
    leads = get_all_leads()
    match = next((l for l in leads if l["email"] == "john@test.com"), None)
    assert match is not None
    assert match["name"] == "John Smith"
