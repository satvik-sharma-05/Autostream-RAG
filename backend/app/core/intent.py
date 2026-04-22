"""Intent classification using keyword matching (Layer 1) + Groq LLM (Layer 2)."""
import json
import re
from typing import Tuple

from groq import AsyncGroq

from app.core.prompts import INTENT_CLASSIFICATION_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Layer 1: Keyword rules (fast, ~0ms) ──────────────────────────────────────
_HIGH_INTENT_KEYWORDS = [
    "sign up", "signup", "subscribe", "buy", "purchase", "get started",
    "start trial", "free trial", "i want the pro", "i want the business",
    "i want to try", "i'm ready", "im ready", "take my money",
    "upgrade", "join now", "i want to sign", "ready to buy",
    "how do i get", "how to get started", "let's go", "lets go",
]

_PRICING_KEYWORDS = [
    "price", "pricing", "cost", "how much", "plans", "plan", "subscription",
    "monthly", "annually", "per month", "per year", "free plan", "pro plan",
    "business plan", "tier", "package",
]

_GREETING_KEYWORDS = ["hello", "hi", "hey", "good morning", "good afternoon", "howdy", "sup", "what's up"]

_FAREWELL_KEYWORDS = ["bye", "goodbye", "see you", "thanks", "thank you", "that's all", "done"]


def _keyword_classify(message: str) -> Tuple[str, float] | None:
    """
    Layer 1: Fast keyword-based classification.
    Returns (intent, confidence) if matched, else None to fall through to LLM.
    """
    lower = message.lower().strip()

    # Single-word plan names typed alone = high purchase intent
    if lower in ("pro", "pro plan", "business", "business plan", "premium"):
        return "high_purchase_intent", 0.90

    if any(kw in lower for kw in _HIGH_INTENT_KEYWORDS):
        return "high_purchase_intent", 0.90

    # Greetings — only if very short message
    if len(lower.split()) <= 4 and any(lower.startswith(kw) for kw in _GREETING_KEYWORDS):
        return "greeting", 0.95

    if any(kw in lower for kw in _FAREWELL_KEYWORDS) and len(lower.split()) <= 6:
        return "farewell", 0.90

    return None  # Fall through to LLM


async def classify_intent(message: str, groq_client: AsyncGroq, model: str) -> Tuple[str, float]:
    """
    Classify user message intent using a two-layer approach:
      Layer 1 — keyword matching (fast, no API call)
      Layer 2 — Groq LLM (nuanced, used only when keywords don't match)

    Returns:
        Tuple of (intent_label, confidence_score)
    """
    # Layer 1
    keyword_result = _keyword_classify(message)
    if keyword_result:
        logger.info(f"Layer 1 keyword match: {keyword_result[0]} ({keyword_result[1]})")
        return keyword_result

    # Layer 2 — LLM
    prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)
    try:
        response = await groq_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            intent = data.get("intent", "off_topic")
            confidence = float(data.get("confidence", 0.5))
            logger.info(f"Layer 2 LLM classification: {intent} ({confidence})")
            return intent, confidence
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
    return "off_topic", 0.5
