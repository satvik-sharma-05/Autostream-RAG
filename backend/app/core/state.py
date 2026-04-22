"""LangGraph conversation state definition."""
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class LeadInfo(TypedDict, total=False):
    name: Optional[str]
    email: Optional[str]
    platform: Optional[str]


class ConversationState(TypedDict):
    """Full state carried through the LangGraph graph."""
    messages: Annotated[list, add_messages]
    session_id: str
    intent: str                  # current detected intent
    intent_confidence: float
    lead_info: LeadInfo          # progressively collected lead fields
    lead_captured: bool          # True once all 3 fields saved
    rag_context: str             # retrieved knowledge base snippets
    turn_count: int
    awaiting_field: Optional[str]  # which field we're currently asking for
