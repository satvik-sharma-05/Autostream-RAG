"""WhatsApp webhook endpoints."""
import os
from fastapi import APIRouter, Request, HTTPException, Query
from app.core.agent import chat
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification handshake."""
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "autostream_verify")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def receive_whatsapp(request: Request):
    """Receive and process incoming WhatsApp messages."""
    try:
        body = await request.json()
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "no_message"}

        msg = messages[0]
        from_number = msg.get("from", "unknown")
        text = msg.get("text", {}).get("body", "")

        if not text:
            return {"status": "non_text_message"}

        result = await chat(session_id=f"wa_{from_number}", user_message=text)
        logger.info(f"WhatsApp message from {from_number}: {text[:50]}")

        # In production: send result["response"] back via WhatsApp Cloud API
        return {"status": "processed", "response": result["response"]}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}
