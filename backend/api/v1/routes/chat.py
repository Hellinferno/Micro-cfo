"""
Chat API Routes
Unified chat interface for all agents
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Literal

from backend.agents.orchestrator import Orchestrator


router = APIRouter()
orchestrator = Orchestrator()


# --- Schemas ---
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str
    agent: Optional[Literal["visual_auditor", "legal_sentinel", "subsidy_hunter", "negotiator", "auto"]] = "auto"
    context: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    success: bool
    message: str
    agent_used: str
    suggested_actions: List[str] = []
    error: Optional[str] = None


# --- Routes ---
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI assistant
    Agent is auto-selected based on message content, or specify explicitly
    """
    try:
        result = await orchestrator.process_message(
            message=request.message,
            preferred_agent=request.agent,
            context=request.context
        )
        return ChatResponse(success=True, **result)
    except Exception as e:
        return ChatResponse(
            success=False,
            message="Sorry, I encountered an error processing your request.",
            agent_used="error",
            error=str(e)
        )


@router.get("/history")
async def get_chat_history():
    """Get user's chat history"""
    # TODO: Implement with database
    return {"messages": [], "total": 0}


@router.delete("/history")
async def clear_chat_history():
    """Clear user's chat history"""
    # TODO: Implement with database
    return {"success": True, "message": "Chat history cleared"}
