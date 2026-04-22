"""Integration tests for API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_endpoint():
    mock_result = {
        "response": "Hello! How can I help you?",
        "intent": "greeting",
        "intent_confidence": 0.99,
        "lead_captured": False,
        "lead_info": {},
        "turn_count": 1,
    }
    with patch("app.api.routes.chat.chat", new=AsyncMock(return_value=mock_result)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"message": "Hello", "session_id": "test-session"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "greeting"
    assert "response" in data


@pytest.mark.asyncio
async def test_leads_endpoint():
    with patch("app.api.routes.leads.get_all_leads", return_value=[
        {"name": "John", "email": "john@test.com", "platform": "YouTube",
         "captured_at": "2025-01-01T00:00:00", "status": "new"}
    ]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/leads")
    assert response.status_code == 200
    assert len(response.json()) == 1
