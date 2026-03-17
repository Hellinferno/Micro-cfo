"""
Chat API - Unified conversational interface for all agents
Orchestrator-based message routing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/chat", tags=["Chat"])


class AgentType(str, Enum):
    """Available agents"""
    AUTO = "auto"
    VISUAL_AUDITOR = "visual_auditor"
    LEGAL_SENTINEL = "legal_sentinel"
    SUBSIDY_HUNTER = "subsidy_hunter"
    NEGOTIATOR = "negotiator"
    GENERAL = "general"


class MessageRole(str, Enum):
    """Message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message"""
    role: MessageRole
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    agent: AgentType = AgentType.AUTO
    context: Optional[List[ChatMessage]] = None
    user_profile: Optional[Dict[str, Any]] = None


class SuggestedAction(BaseModel):
    """Suggested follow-up action"""
    label: str
    action_type: str
    payload: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response"""
    message: str
    agent_used: AgentType
    confidence_score: float
    suggested_actions: Optional[List[SuggestedAction]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send message to MicroCFO chat
    
    The Orchestrator automatically routes to the appropriate agent:
    - Invoice/scan questions → Visual Auditor (Agent A)
    - Compliance/legal questions → Legal Sentinel (Agent B)
    - Subsidy/scheme questions → Subsidy Hunter (Agent C)
    - Negotiation/payment questions → Negotiator (Agent D)
    - General questions → General LLM
    
    Supports conversation context for multi-turn dialogues
    """
    try:
        from backend.agents.orchestrator import process_message
        
        # Convert context to dict format
        context_list = []
        if request.context:
            context_list = [msg.dict() for msg in request.context]
        
        # Process with Orchestrator
        result = await process_message(
            message=request.message,
            preferred_agent=request.agent.value,
            context=context_list,
            user_profile=request.user_profile
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history by ID
    
    Returns complete conversation with all messages
    """
    # TODO: Implement conversation retrieval
    return {
        "success": True,
        "data": {
            "conversation_id": conversation_id,
            "messages": [],
            "total_messages": 0
        }
    }


@router.get("/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 20
):
    """
    List user conversations
    
    Returns paginated list of conversations
    """
    # TODO: Implement conversation listing
    return {
        "success": True,
        "data": {
            "conversations": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation
    
    Removes conversation and all associated messages
    """
    # TODO: Implement conversation deletion
    return {
        "success": True,
        "message": f"Conversation {conversation_id} deleted"
    }


@router.post("/clear")
async def clear_conversation():
    """
    Clear current conversation context
    
    Resets conversation state for fresh start
    """
    return {
        "success": True,
        "message": "Conversation context cleared"
    }


@router.get("/agents")
async def list_available_agents():
    """
    List available AI agents and their capabilities
    
    Returns information about each agent's specialty
    """
    agents = {
        AgentType.VISUAL_AUDITOR.value: {
            "name": "Visual Auditor",
            "description": "Invoice analysis and fraud detection",
            "capabilities": [
                "Invoice data extraction",
                "Fraud detection (tampering, handwriting)",
                "ITC compliance checking",
                "Line item categorization"
            ]
        },
        AgentType.LEGAL_SENTINEL.value: {
            "name": "Legal Sentinel",
            "description": "Legal compliance monitoring",
            "capabilities": [
                "GST compliance checking",
                "Income tax guidance",
                "Companies Act compliance",
                "Real-time legal updates"
            ]
        },
        AgentType.SUBSIDY_HUNTER.value: {
            "name": "Subsidy Hunter",
            "description": "Government scheme discovery",
            "capabilities": [
                "Scheme matching by sector",
                "CAPEX-based filtering",
                "State-specific schemes",
                "Eligibility assessment"
            ]
        },
        AgentType.NEGOTIATOR.value: {
            "name": "Negotiator",
            "description": "Vendor negotiation assistance",
            "capabilities": [
                "Email draft generation",
                "A/B testing variations",
                "Cash flow analysis",
                "Multi-format output (email, Telegram)"
            ]
        },
        AgentType.GENERAL.value: {
            "name": "General Assistant",
            "description": "General financial queries",
            "capabilities": [
                "General Q&A",
                "Basic calculations",
                "Information lookup"
            ]
        }
    }
    
    return {
        "success": True,
        "data": {
            "agents": agents,
            "default": AgentType.AUTO.value
        }
    }
