"""
Orchestrator - Intelligent Message Routing
Routes user messages to appropriate AI agents
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Available agents"""
    AUTO = "auto"
    VISUAL_AUDITOR = "visual_auditor"
    LEGAL_SENTINEL = "legal_sentinel"
    SUBSIDY_HUNTER = "subsidy_hunter"
    NEGOTIATOR = "negotiator"
    GENERAL = "general"


# Keyword mapping for agent selection
AGENT_KEYWORDS = {
    AgentType.VISUAL_AUDITOR: [
        "invoice", "bill", "scan", "upload", "document", "image", "photo",
        "vendor", "gst", "tax invoice", "receipt", "purchase", "capital goods"
    ],
    AgentType.LEGAL_SENTINEL: [
        "compliance", "legal", "law", "section", "act", "gst", "tax", "itc",
        "credit", "input tax", "penalty", "fine", "notification", "rule",
        "eligible", "blocked", "exempt", "taxable"
    ],
    AgentType.SUBSIDY_HUNTER: [
        "subsidy", "scheme", "grant", "funding", "loan", "incentive",
        "government", "plI", "tufs", "msme", "support", "benefit",
        "scheme", "application", "eligibility"
    ],
    AgentType.NEGOTIATOR: [
        "negotiate", "email", "draft", "vendor", "payment", "credit",
        "extension", "overdue", "chase", "reminder", "early payment",
        "discount", "terms", "counterparty"
    ]
}


async def process_message(
    message: str,
    preferred_agent: str = "auto",
    context: Optional[List[Dict[str, str]]] = None,
    user_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process user message and route to appropriate agent
    
    Args:
        message: User's message text
        preferred_agent: User-specified agent (or "auto" for automatic routing)
        context: Conversation history for context
        user_profile: User profile data (turnover, sector, etc.)
    
    Returns:
        Agent response with message and metadata
    """
    # Determine which agent to use
    if preferred_agent and preferred_agent != "auto":
        agent = preferred_agent
    else:
        agent = _determine_agent_from_message(message)
    
    # Process with selected agent
    try:
        if agent == AgentType.VISUAL_AUDITOR.value:
            result = await _handle_invoice_question(message, context, user_profile)
        elif agent == AgentType.LEGAL_SENTINEL.value:
            result = await _handle_compliance(message, context, user_profile)
        elif agent == AgentType.SUBSIDY_HUNTER.value:
            result = await _handle_subsidies(message, context, user_profile)
        elif agent == AgentType.NEGOTIATOR.value:
            result = await _handle_negotiation(message, context, user_profile)
        else:
            result = await _handle_general(message, context, user_profile)
        
        # Add metadata
        result["agent_used"] = agent
        result["confidence_score"] = result.get("confidence_score", 0.8)
        
        # Add suggested actions
        result["suggested_actions"] = _get_suggested_actions(agent, result)
        
        return result
    
    except Exception as e:
        print(f"Error processing message with agent {agent}: {e}")
        return {
            "message": f"I encountered an error processing your request. Please try again or rephrase your question.",
            "agent_used": agent,
            "confidence_score": 0.5,
            "suggested_actions": [],
            "metadata": {"error": str(e)}
        }


def _determine_agent_from_message(message: str) -> str:
    """Determine which agent should handle the message"""
    message_lower = message.lower()
    
    # Score each agent based on keyword matches
    scores = {}
    for agent, keywords in AGENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in message_lower)
        scores[agent.value] = score
    
    # Select agent with highest score
    if max(scores.values()) == 0:
        return AgentType.GENERAL.value
    
    best_agent = max(scores, key=scores.get)
    return best_agent


async def _handle_compliance(
    message: str,
    context: Optional[List[Dict[str, str]]],
    user_profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle compliance/legal questions with Agent B"""
    from backend.agents.legal_sentinel import check_compliance_law
    
    result = await check_compliance_law(message, user_profile)
    
    # Format response
    explanation = result.get("explanation", "")
    sections = result.get("relevant_sections", [])
    
    sections_text = ""
    if sections:
        sections_text = "\n\nRelevant Sections:\n"
        for section in sections[:3]:
            sections_text += f"• {section.get('section_number', '')} - {section.get('act_name', '')}\n"
    
    warnings_text = ""
    if result.get("warnings"):
        warnings_text = "\n\n⚠️ Warnings:\n" + "\n".join(f"• {w}" for w in result["warnings"][:2])
    
    full_message = f"{explanation}{sections_text}{warnings_text}"
    
    return {
        "message": full_message,
        "metadata": {
            "risk_level": result.get("risk_level", "UNKNOWN"),
            "sections": sections
        }
    }


async def _handle_subsidies(
    message: str,
    context: Optional[List[Dict[str, str]]],
    user_profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle subsidy questions with Agent C"""
    from backend.agents.subsidy_hunter import find_subsidies
    
    # Extract sector from message or profile
    sector = user_profile.get("business_sector") if user_profile else None
    
    # Search for subsidies
    schemes = await find_subsidies(sector=sector, query=message)
    
    # Format response
    if not schemes:
        return {
            "message": "I couldn't find specific subsidies matching your criteria. Try providing more details about your sector or investment amount.",
            "metadata": {"schemes": []}
        }
    
    schemes_text = "Here are some relevant government schemes:\n\n"
    for i, scheme in enumerate(schemes[:5], 1):
        schemes_text += f"{i}. **{scheme.get('name', 'Unknown')}**\n"
        schemes_text += f"   Benefit: {scheme.get('benefit', 'N/A')}\n"
        schemes_text += f"   Eligibility: {scheme.get('eligibility', 'N/A')}\n"
        if scheme.get('link'):
            schemes_text += f"   Link: {scheme.get('link')}\n"
        schemes_text += "\n"
    
    return {
        "message": schemes_text,
        "metadata": {
            "schemes": schemes,
            "total_matches": len(schemes)
        }
    }


async def _handle_invoice_question(
    message: str,
    context: Optional[List[Dict[str, str]]],
    user_profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle invoice-related questions"""
    # Check if user is asking about invoice analysis
    if any(word in message.lower() for word in ["scan", "upload", "analyze"]):
        return {
            "message": "I can help you analyze invoices! Please upload an invoice image (PNG, JPG, or PDF) using the document scanner, and I'll extract the data, check for fraud indicators, and identify compliance issues.",
            "metadata": {"action_required": "upload_invoice"}
        }
    else:
        return {
            "message": "I can help with invoice analysis and compliance. You can:\n\n"
                      "• Upload invoices for automated analysis\n"
                      "• Check ITC eligibility\n"
                      "• Detect fraud indicators\n"
                      "• Categorize expenses\n\n"
                      "What would you like to do?",
            "metadata": {}
        }


async def _handle_negotiation(
    message: str,
    context: Optional[List[Dict[str, str]]],
    user_profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle negotiation requests with Agent D"""
    from backend.agents.negotiator import generate_negotiation
    
    # Extract invoice data from context or message
    # This is simplified - in production, would parse more carefully
    invoice_data = {
        "vendor_name": "Vendor",
        "invoice_number": "INV-XXX",
        "amount": 0,
        "due_date": ""
    }
    
    negotiation_context = message
    
    result = await generate_negotiation(
        invoice_data=invoice_data,
        negotiation_context=negotiation_context,
        vendor_relationship="neutral",
        tone="professional",
        generate_variations=True
    )
    
    primary = result.get("primary_draft", {})
    
    response_text = "I've generated a negotiation draft for you:\n\n"
    response_text += f"**Subject:** {primary.get('subject', 'N/A')}\n\n"
    response_text += f"**Strategy:** {primary.get('strategy_explanation', 'N/A')}\n\n"
    
    if result.get("alternative_draft") and primary.get('variation_id') == 'primary':
        alt = result["alternative_draft"]
        response_text += f"**Alternative Approach:**\n"
        response_text += f"Subject: {alt.get('subject', 'N/A')}\n"
        response_text += f"Strategy: {alt.get('strategy_explanation', 'N/A')}\n\n"
    
    response_text += "Would you like me to customize this draft further?"
    
    return {
        "message": response_text,
        "metadata": {
            "drafts": result,
            "intent": primary.get("intent", "unknown")
        }
    }


async def _handle_general(
    message: str,
    context: Optional[List[Dict[str, str]]],
    user_profile: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Handle general questions using LLM"""
    try:
        import google.generativeai as genai
        
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Build prompt with context
            prompt = f"""You are MicroCFO, an AI-powered financial assistant for Indian MSMEs.

Specializations:
- GST compliance and ITC eligibility
- Government subsidies and schemes
- Invoice analysis and fraud detection
- Vendor negotiation assistance

User Profile: {json.dumps(user_profile) if user_profile else 'Not provided'}

Answer the following question concisely and professionally:

{message}

If the question requires specialized analysis (invoice scanning, legal compliance, subsidy search, or negotiation), mention that and guide the user to the appropriate feature."""
            
            response = model.generate_content(prompt)
            
            return {
                "message": response.text,
                "metadata": {"source": "general_llm"}
            }
    
    except Exception as e:
        print(f"Error in general handler: {e}")
    
    # Fallback response
    return {
        "message": "I'm MicroCFO, your AI financial assistant. I can help with:\n\n"
                  "• 📄 Invoice Analysis - Upload invoices for automated processing\n"
                  "• ⚖️ Compliance Checking - GST, ITC, and legal guidance\n"
                  "• 💰 Subsidy Discovery - Find government schemes for your business\n"
                  "• 📧 Negotiation Assistance - Draft vendor communications\n\n"
                  "What would you like help with today?",
        "metadata": {"source": "fallback"}
    }


def _get_suggested_actions(
    agent: str,
    result: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate suggested follow-up actions"""
    actions = []
    
    if agent == AgentType.LEGAL_SENTINEL.value:
        actions.append({
            "label": "Save Answer",
            "action_type": "save",
            "payload": {"type": "compliance_response"}
        })
        actions.append({
            "label": "Check Related Sections",
            "action_type": "search",
            "payload": {"query": "related sections"}
        })
    
    elif agent == AgentType.SUBSIDY_HUNTER.value:
        schemes = result.get("metadata", {}).get("schemes", [])
        if schemes:
            actions.append({
                "label": "View All Schemes",
                "action_type": "navigate",
                "payload": {"page": "/subsidies"}
            })
            actions.append({
                "label": "Check Eligibility",
                "action_type": "check_eligibility",
                "payload": {"scheme": schemes[0].get("name") if schemes else None}
            })
    
    elif agent == AgentType.NEGOTIATOR.value:
        actions.append({
            "label": "Copy Email",
            "action_type": "copy",
            "payload": {"type": "email_draft"}
        })
        actions.append({
            "label": "Send via Email",
            "action_type": "send_email",
            "payload": {}
        })
    
    elif agent == AgentType.VISUAL_AUDITOR.value:
        actions.append({
            "label": "Upload Invoice",
            "action_type": "navigate",
            "payload": {"page": "/scanner"}
        })
    
    return actions


def initialize_orchestrator():
    """Initialize the Orchestrator"""
    print("Orchestrator initialized")
    return True
