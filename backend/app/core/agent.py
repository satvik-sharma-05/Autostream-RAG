"""LangGraph agent orchestration for AutoStream."""
import os
import re
from typing import Optional

from groq import AsyncGroq
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.core.state import ConversationState
from app.core.intent import classify_intent
from app.core.rag import retrieve_context
from app.core.tools import capture_lead
from app.core.prompts import SYSTEM_PROMPT
from app.utils.validators import is_valid_email
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Groq async client for intent classification
_groq_client: Optional[AsyncGroq] = None
_graph = None
_checkpointer = None


def _get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def _get_llm(model_override: str = None) -> ChatGroq:
    model = model_override or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=model,
        temperature=float(os.getenv("TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "500")),
    )


async def _invoke_llm_with_fallback(messages: list) -> str:
    """Try primary model, fall back to faster model on rate limit."""
    primary = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    fallback = "llama-3.1-8b-instant"
    for model in [primary, fallback]:
        try:
            llm = _get_llm(model)
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            if "429" in str(e) or "rate_limit_exceeded" in str(e):
                if model == fallback:
                    raise  # both exhausted
                logger.warning(f"Rate limit on {model}, trying {fallback}")
                continue
            raise


# ── Graph nodes ──────────────────────────────────────────────────────────────

async def classify_node(state: ConversationState) -> dict:
    """Classify intent of the latest user message."""
    messages = state["messages"]
    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)), ""
    )
    groq = _get_groq_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    intent, confidence = await classify_intent(last_human, groq, model)
    logger.info(f"Intent: {intent} ({confidence:.2f})")
    return {"intent": intent, "intent_confidence": confidence}


async def rag_node(state: ConversationState) -> dict:
    """Retrieve relevant context from ChromaDB."""
    messages = state["messages"]
    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)), ""
    )
    context = retrieve_context(last_human)
    return {"rag_context": context}


def _parse_lead_fields(text: str) -> dict:
    """
    Extract name, email, and/or platform from a free-form message.
    Handles formats like:
      - "Name: Satvik Email: foo@bar.com"
      - "Name : Satvik / Email: foo@bar.com"
      - "Satvik, foo@bar.com"
      - plain email "foo@bar.com"
      - plain name "Satvik Sharma"
    Returns a dict with only the keys that were found.
    """
    found: dict = {}
    t = text.strip()

    # Extract email anywhere in the message (most reliable signal)
    email_match = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", t)
    if email_match:
        found["email"] = email_match.group(0).strip().lower()

    # Extract explicit "Name: ..." label (strip the label, keep only the value)
    name_label = re.search(
        r"(?:^|[\s,/])(?:[Nn]ame\s*:?\s*)([A-Za-z][A-Za-z\s]{1,40}?)(?=\s*[/,]|\s*[Ee]mail|\s*$)",
        t,
    )
    if name_label:
        raw_name = name_label.group(1).strip()
        # Reject if it looks like an email or is empty
        if raw_name and "@" not in raw_name:
            found["name"] = raw_name

    # Extract explicit "Platform: ..." label
    platform_label = re.search(r"[Pp]latform\s*:?\s*(\w+)", t)
    if platform_label:
        found["platform"] = platform_label.group(1).strip().capitalize()

    # If no name label found but no email either → whole message is probably the name
    if "name" not in found and "email" not in found:
        # Must be short, no special chars, not a question
        if len(t.split()) <= 5 and "@" not in t and "?" not in t:
            found["name"] = t

    # Detect platform keywords if not already found — fuzzy match for typos
    if "platform" not in found:
        _PLATFORMS = {
            "youtube": "YouTube",
            "tiktok": "TikTok",
            "instagram": "Instagram",
            "facebook": "Facebook",
            "twitter": "Twitter",
            "linkedin": "LinkedIn",
            "twitch": "Twitch",
        }
        t_lower = t.lower()
        for key, display in _PLATFORMS.items():
            # exact substring OR starts-with match (catches "instagaram", "youtub", etc.)
            if key in t_lower or t_lower.startswith(key[:5]):
                found["platform"] = display
                break

    return found


def _clean_name(raw: str) -> str:
    """Strip any 'Name:' prefix and title-case the result."""
    cleaned = re.sub(r"^[Nn]ame\s*:?\s*", "", raw).strip()
    return cleaned.title() if cleaned else raw


def _looks_like_question(text: str) -> bool:
    """Return True if the user appears to be asking a question rather than providing info."""
    t = text.strip().lower()
    question_starters = ("what", "how", "why", "who", "when", "where", "which", "can", "do", "does",
                         "is ", "are ", "tell me", "explain", "show me", "?")
    return t.endswith("?") or any(t.startswith(s) for s in question_starters)


async def lead_collection_node(state: ConversationState) -> dict:
    """
    Handle progressive lead field collection.
    - Parses the user message for any fields (name/email/platform) in any format.
    - Skips asking for fields already extracted.
    - If the user asks a question mid-collection, answers it then re-asks the pending field.
    """
    messages = state["messages"]
    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)), ""
    ).strip()

    lead_info = dict(state.get("lead_info", {}))
    awaiting = state.get("awaiting_field")

    # ── If user is asking a question, answer it and re-ask the pending field ──
    if _looks_like_question(last_human):
        rag_context = retrieve_context(last_human)
        system_content = SYSTEM_PROMPT.format(rag_context=rag_context or "No specific context retrieved.")
        content = await _invoke_llm_with_fallback(
            [SystemMessage(content=system_content)] + list(messages[-10:])
        )
        field_prompts = {
            "name": "By the way, could I get your name so our team can follow up?",
            "email": "And what's the best email address to reach you at?",
            "platform": "Which platform do you primarily create content on? (YouTube, TikTok, Instagram, etc.)",
        }
        re_ask = f"\n\n{field_prompts[awaiting]}" if awaiting in field_prompts else ""
        return {
            "messages": [AIMessage(content=content + re_ask)],
            "rag_context": rag_context,
            "awaiting_field": awaiting,
            "turn_count": state.get("turn_count", 0) + 1,
        }

    # ── Parse the message for any lead fields ────────────────────────────────
    parsed = _parse_lead_fields(last_human)

    # Merge parsed fields into lead_info (don't overwrite already-collected fields)
    for field in ("name", "email", "platform"):
        if field not in lead_info and field in parsed:
            lead_info[field] = parsed[field]

    # Clean the name if it has a "Name:" prefix artifact
    if "name" in lead_info:
        lead_info["name"] = _clean_name(lead_info["name"])

    # ── Decide what to ask next ───────────────────────────────────────────────
    if not lead_info.get("name"):
        awaiting = "name"
        response = "Could I get your name so our team can follow up with you?"

    elif not lead_info.get("email"):
        awaiting = "email"
        name = lead_info["name"]
        response = f"Thanks {name}! What's your email address?"

    elif not lead_info.get("platform"):
        awaiting = "platform"
        response = "Great! Which platform do you primarily create content for? (YouTube, TikTok, Instagram, etc.)"

    else:
        # All three fields collected — fire the lead capture tool
        awaiting = None
        result = capture_lead.invoke({
            "name": lead_info["name"],
            "email": lead_info["email"],
            "platform": lead_info["platform"],
        })
        response = (
            f"Perfect! I've got everything I need. {result} "
            f"Is there anything else I can help you with today?"
        )
        return {
            "messages": [AIMessage(content=response)],
            "lead_info": lead_info,
            "lead_captured": True,
            "awaiting_field": None,
            "turn_count": state.get("turn_count", 0) + 1,
        }

    return {
        "messages": [AIMessage(content=response)],
        "lead_info": lead_info,
        "awaiting_field": awaiting,
        "turn_count": state.get("turn_count", 0) + 1,
    }


async def llm_node(state: ConversationState) -> dict:
    """Generate LLM response using Groq + RAG context."""
    rag_context = state.get("rag_context", "")
    intent = state.get("intent", "")
    lead_info = state.get("lead_info", {})

    system_content = SYSTEM_PROMPT.format(rag_context=rag_context or "No specific context retrieved.")

    # Build message history for LLM (last 10 turns)
    history = state["messages"][-10:]
    llm_messages = [SystemMessage(content=system_content)] + list(history)

    response_text = await _invoke_llm_with_fallback(llm_messages)

    updates: dict = {
        "messages": [AIMessage(content=response_text)],
        "turn_count": state.get("turn_count", 0) + 1,
    }

    # ONLY trigger lead collection on explicit high purchase intent.
    # Guard against ambiguous single-word replies like "yes"/"ok" which are
    # continuations of conversation, not fresh purchase signals.
    _AMBIGUOUS = {"yes", "yeah", "yep", "ok", "okay", "sure", "yup", "no", "nope"}
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
    ).strip().lower()
    last_human_raw = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
    ).strip()

    HIGH_INTENT = {"high_purchase_intent"}
    if (intent in HIGH_INTENT
            and not state.get("lead_captured")
            and last_human not in _AMBIGUOUS):
        if not lead_info.get("name"):
            updates["messages"] = [AIMessage(
                content="Great choice! To get you connected with our team, could I start with your name?"
            )]
            updates["awaiting_field"] = "name"

    # If user provided name+email in a single message while NOT in collection mode,
    # parse and start collection so it doesn't get lost in the LLM response
    if not state.get("awaiting_field") and not state.get("lead_captured"):
        parsed = _parse_lead_fields(last_human_raw)
        if parsed.get("name") and parsed.get("email"):
            merged = dict(lead_info)
            for f in ("name", "email", "platform"):
                if f not in merged and f in parsed:
                    merged[f] = parsed[f]
            if "name" in merged:
                merged["name"] = _clean_name(merged["name"])
            updates["lead_info"] = merged
            if not merged.get("platform"):
                updates["awaiting_field"] = "platform"
                updates["messages"] = [AIMessage(
                    content=f"Thanks {merged['name']}! Which platform do you primarily create content for? (YouTube, TikTok, Instagram, etc.)"
                )]
            else:
                result = capture_lead.invoke({
                    "name": merged["name"],
                    "email": merged["email"],
                    "platform": merged["platform"],
                })
                updates["lead_captured"] = True
                updates["awaiting_field"] = None
                updates["messages"] = [AIMessage(
                    content=f"Perfect! I've got everything I need. {result} Is there anything else I can help you with today?"
                )]

    return updates


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_classify(state: ConversationState) -> str:
    """Route to lead collection if we're mid-collection, else RAG + LLM."""
    if state.get("awaiting_field") and not state.get("lead_captured"):
        return "lead_collection"
    return "rag"


# ── Graph builder ─────────────────────────────────────────────────────────────

async def build_graph():
    """Build and compile the LangGraph state machine."""
    global _graph, _checkpointer

    checkpoint_path = os.getenv("CHECKPOINTER_PATH", "./data/checkpoints.db")

    # Use MemorySaver for simplicity; swap for AsyncSqliteSaver in production
    from langgraph.checkpoint.memory import MemorySaver
    _checkpointer = MemorySaver()

    builder = StateGraph(ConversationState)
    builder.add_node("classify", classify_node)
    builder.add_node("rag", rag_node)
    builder.add_node("lead_collection", lead_collection_node)
    builder.add_node("llm", llm_node)

    builder.set_entry_point("classify")
    builder.add_conditional_edges("classify", route_after_classify, {
        "lead_collection": "lead_collection",
        "rag": "rag",
    })
    builder.add_edge("rag", "llm")
    builder.add_edge("llm", END)
    builder.add_edge("lead_collection", END)

    _graph = builder.compile(checkpointer=_checkpointer)
    logger.info("LangGraph agent compiled successfully.")
    return _graph


async def get_graph():
    global _graph
    if _graph is None:
        await build_graph()
    return _graph


async def chat(session_id: str, user_message: str) -> dict:
    """
    Process a user message and return the agent's response.

    Args:
        session_id: Unique conversation session identifier
        user_message: The user's input text

    Returns:
        dict with 'response', 'intent', 'lead_captured', 'lead_info'
    """
    graph = await get_graph()
    config = {"configurable": {"thread_id": session_id}}

    # Check if there's existing state for this session
    existing = await graph.aget_state(config)
    if existing and existing.values:
        # Resume existing conversation — only send the new message
        input_state = {"messages": [HumanMessage(content=user_message)]}
    else:
        # New conversation — initialize full state
        input_state = {
            "messages": [HumanMessage(content=user_message)],
            "session_id": session_id,
            "intent": "",
            "intent_confidence": 0.0,
            "lead_info": {},
            "lead_captured": False,
            "rag_context": "",
            "turn_count": 0,
            "awaiting_field": None,
        }

    result = await graph.ainvoke(input_state, config=config)

    # Extract last AI message
    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    response_text = ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't process that."

    return {
        "response": response_text,
        "intent": result.get("intent", ""),
        "intent_confidence": result.get("intent_confidence", 0.0),
        "lead_captured": result.get("lead_captured", False),
        "lead_info": result.get("lead_info", {}),
        "turn_count": result.get("turn_count", 0),
    }
