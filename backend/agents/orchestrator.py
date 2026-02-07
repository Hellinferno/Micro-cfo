"""
Orchestrator - The Brain
Routes user messages to appropriate agents
"""

import os
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel

from backend.agents.visual_auditor import VisualAuditor
from backend.agents.legal_sentinel import LegalSentinel
from backend.agents.subsidy_hunter import SubsidyHunter


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class Orchestrator:
    """
    The Brain: Routes messages to appropriate agents
    """
    
    def __init__(self):
        self.visual_auditor = VisualAuditor()
        self.legal_sentinel = LegalSentinel()
        self.subsidy_hunter = SubsidyHunter()
    
    async def process_message(
        self,
        message: str,
        preferred_agent: Optional[str] = "auto",
        context: Optional[List[ChatMessage]] = None
    ) -> Dict[str, Any]:
        """Process user message and route to appropriate agent"""
        
        # Determine which agent to use
        agent = self._determine_agent(message, preferred_agent)
        
        if agent == "legal_sentinel":
            result = await self._handle_compliance(message)
        elif agent == "subsidy_hunter":
            result = await self._handle_subsidies(message)
        elif agent == "visual_auditor":
            result = await self._handle_invoice_question(message)
        else:
            result = await self._handle_general(message)
        
        return result
    
    def _determine_agent(self, message: str, preferred: Optional[str]) -> str:
        """Determine which agent should handle the message"""
        
        if preferred and preferred != "auto":
            return preferred
        
        msg_lower = message.lower()
        
        # Compliance/Legal keywords
        compliance_keywords = [
            "gst", "tax", "itc", "input tax", "compliance", "gstr", "filing",
            "penalty", "section", "act", "law", "legal", "audit", "eway",
            "invoice", "compliance", "registration", "return"
        ]
        
        # Subsidy keywords
        subsidy_keywords = [
            "subsidy", "scheme", "grant", "loan", "pmegp", "mudra", "credit",
            "funding", "government", "msme", "startup", "incentive", "benefit",
            "eligibility", "apply", "application"
        ]
        
        # Invoice/document keywords
        invoice_keywords = [
            "scan", "upload", "invoice", "bill", "receipt", "document",
            "vendor", "payment", "amount", "analyze"
        ]
        
        # Score each category
        compliance_score = sum(1 for kw in compliance_keywords if kw in msg_lower)
        subsidy_score = sum(1 for kw in subsidy_keywords if kw in msg_lower)
        invoice_score = sum(1 for kw in invoice_keywords if kw in msg_lower)
        
        # Return agent with highest score
        if compliance_score > subsidy_score and compliance_score > invoice_score:
            return "legal_sentinel"
        elif subsidy_score > compliance_score and subsidy_score > invoice_score:
            return "subsidy_hunter"
        elif invoice_score > 0:
            return "visual_auditor"
        
        # Default to legal sentinel for general questions
        return "legal_sentinel"
    
    async def _handle_compliance(self, message: str) -> Dict[str, Any]:
        """Handle compliance questions"""
        result = await self.legal_sentinel.analyze(message)
        
        return {
            "message": f"**{result.risk_level} Risk**\n\n"
                      f"📖 **{result.relevant_section}**\n\n"
                      f"{result.explanation}\n\n"
                      f"✅ **Action:** {result.compliant_action}",
            "agent_used": "legal_sentinel",
            "suggested_actions": [
                "Check related sections",
                "Save this answer",
                "Ask follow-up question"
            ]
        }
    
    async def _handle_subsidies(self, message: str) -> Dict[str, Any]:
        """Handle subsidy queries"""
        # Extract basic info from message (simplified)
        sector = "Manufacturing"  # Default
        capex = 500000  # Default
        
        if "textile" in message.lower():
            sector = "Textile"
        elif "food" in message.lower():
            sector = "Food Processing"
        elif "tech" in message.lower() or "it" in message.lower():
            sector = "IT/Technology"
        
        schemes = await self.subsidy_hunter.find_subsidies(sector, capex)
        
        if not schemes:
            return {
                "message": "I couldn't find matching schemes. Please use the Subsidy Explorer for detailed search.",
                "agent_used": "subsidy_hunter",
                "suggested_actions": ["Open Subsidy Explorer", "Refine search criteria"]
            }
        
        # Format schemes
        scheme_list = "\n\n".join([
            f"**{s.name}**\n"
            f"💰 {s.benefit}\n"
            f"✅ {s.eligibility}\n"
            f"🏛️ {s.ministry}"
            + (f"\n🔗 [Apply]({s.link})" if s.link else "")
            for s in schemes[:3]
        ])
        
        return {
            "message": f"Found {len(schemes)} applicable schemes:\n\n{scheme_list}",
            "agent_used": "subsidy_hunter",
            "suggested_actions": [
                "View all schemes",
                "Check eligibility",
                "Start application"
            ]
        }
    
    async def _handle_invoice_question(self, message: str) -> Dict[str, Any]:
        """Handle invoice-related questions"""
        return {
            "message": "To analyze an invoice, please upload the document using the Document Scanner. "
                      "I can help you understand invoice details, detect fraud indicators, and check compliance.",
            "agent_used": "visual_auditor",
            "suggested_actions": [
                "Open Document Scanner",
                "Upload invoice",
                "View recent scans"
            ]
        }
    
    async def _handle_general(self, message: str) -> Dict[str, Any]:
        """Handle general questions"""
        return {
            "message": "I'm MicroCFO, your AI financial assistant. I can help you with:\n\n"
                      "📄 **Invoice Scanning** - Analyze invoices for fraud & compliance\n"
                      "⚖️ **Compliance Check** - Get answers on GST, tax laws\n"
                      "💰 **Subsidy Discovery** - Find government schemes for your business\n\n"
                      "What would you like help with?",
            "agent_used": "orchestrator",
            "suggested_actions": [
                "Scan an invoice",
                "Ask a compliance question",
                "Find subsidies"
            ]
        }
