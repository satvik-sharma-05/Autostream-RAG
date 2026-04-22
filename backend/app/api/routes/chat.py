"""Chat API endpoints."""
import uuid
from fastapi import APIRouter, HTTPException, Request
from app.schemas.chat import ChatRequest, ChatResponse
from app.core.agent import chat
from app.utils.logger import get_logger
from app.utils.rate_limiter import limiter

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat_endpoint(request: Request, body: ChatRequest):
    """
    Send a message to the AutoStream AI agent.
    Returns the agent's response with intent and lead capture status.
    """
    session_id = body.session_id or str(uuid.uuid4())
    try:
        result = await chat(session_id=session_id, user_message=body.message)
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            intent=result["intent"],
            intent_confidence=result["intent_confidence"],
            lead_captured=result["lead_captured"],
            turn_count=result["turn_count"],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
