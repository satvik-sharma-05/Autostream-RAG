"""Unit tests for intent classification."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.intent import classify_intent


@pytest.mark.asyncio
async def test_classify_pricing_intent():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"intent": "pricing_inquiry", "confidence": 0.95}'))]
    )
    intent, confidence = await classify_intent("What are your plans?", mock_client, "test-model")
    assert intent == "pricing_inquiry"
    assert confidence == 0.95


@pytest.mark.asyncio
async def test_classify_greeting():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"intent": "greeting", "confidence": 0.99}'))]
    )
    intent, confidence = await classify_intent("Hello!", mock_client, "test-model")
    assert intent == "greeting"


@pytest.mark.asyncio
async def test_classify_fallback_on_error():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")
    intent, confidence = await classify_intent("some message", mock_client, "test-model")
    assert intent == "off_topic"
    assert confidence == 0.5
