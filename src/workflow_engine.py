#!/usr/bin/env python3
"""
Enhanced Workflow Engine for MicroCFO - "The Brain"
Implements the complete document lifecycle from the PRD:

1. Visual Audit (Agent A)
2. State Persistence (WorkflowState)
3. Decision Logic (Check thresholds)
4. Proactive Intelligence (Agent C auto-trigger)
5. Legal Compliance Check (Agent B auto-trigger)
6. Negotiation (Agent D) if needed
7. Human Approval

PRD Requirements:
- Auto-trigger Agent C for capital goods > ₹1 Lakh
- Auto-trigger Agent B for personal/entertainment items
- Conservative CA-style recommendations
- Confidence threshold 0.7 triggers manual review
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow statuses as defined in PRD"""
    PENDING = "PENDING"
    AUDIT_COMPLETE = "AUDIT_COMPLETE"
    SUBSIDY_CHECK_TRIGGERED = "SUBSIDY_CHECK_TRIGGERED"
    COMPLIANCE_CHECK_TRIGGERED = "COMPLIANCE_CHECK_TRIGGERED"
    NEGOTIATION_SUGGESTED = "NEGOTIATION_SUGGESTED"
    NEGOTIATION_DRAFTED = "NEGOTIATION_DRAFTED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class WorkflowStep(str, Enum):
    """Individual workflow steps"""
    VISUAL_AUDIT = "visual_audit"
    CONFIDENCE_CHECK = "confidence_check"
    SUBSIDY_CHECK = "subsidy_check"
    COMPLIANCE_CHECK = "compliance_check"
    NEGOTIATION_DECISION = "negotiation_decision"
    NEGOTIATION_DRAFT = "negotiation_draft"
    HUMAN_REVIEW = "human_review"
    FINALIZATION = "finalization"


@dataclass
class WorkflowDecision:
    """Represents a decision made during workflow"""
    step: WorkflowStep
    decision: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    triggered_agent: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "step": self.step.value,
            "decision": self.decision,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "triggered_agent": self.triggered_agent,
            "data": self.data
        }


@dataclass  
class WorkflowResult:
    """Complete workflow execution result"""
    workflow_id: str
    status: WorkflowStatus
    invoice_data: Dict[str, Any]
    decisions: List[WorkflowDecision] = field(default_factory=list)
    subsidy_alerts: List[Dict] = field(default_factory=list)
    compliance_alerts: List[Dict] = field(default_factory=list)
    negotiation_draft: Optional[Dict] = None
    requires_review: bool = False
    review_reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


# PRD Thresholds
CAPITAL_GOODS_THRESHOLD = 100000  # ₹1 Lakh triggers subsidy check
NEGOTIATION_AMOUNT_THRESHOLD = 50000  # ₹50k triggers negotiation consideration
CONFIDENCE_THRESHOLD = 0.7  # Below this requires manual review
HIGH_AMOUNT_FLAG_THRESHOLD = 50000  # ₹50k flagged as high amount


class WorkflowEngine:
    """
    The Brain - Orchestrates multi-step agent workflows
    
    Implements the document lifecycle from PRD:
    1. Process invoice through Agent A
    2. Evaluate confidence and flag for review if needed
    3. Auto-trigger subsidy check for capital goods
    4. Auto-trigger compliance check for personal items
    5. Decide on negotiation based on vendor profile and amount
    6. Wait for human approval on drafts
    """
    
    def __init__(
        self, 
        mcp_bridge = None,
        proactive_engine = None,
        db_session = None
    ):
        """
        Initialize the workflow engine
        
        Args:
            mcp_bridge: MCPBridge instance for calling agents
            proactive_engine: ProactiveIntelligenceEngine instance
            db_session: SQLAlchemy session for persistence
        """
        self.mcp_bridge = mcp_bridge
        self.proactive_engine = proactive_engine
        self.db = db_session
        
    async def process_document_lifecycle(
        self,
        image_url: str,
        user_id: str,
        business_profile: Optional[Dict] = None
    ) -> WorkflowResult:
        """
        Execute complete document lifecycle as defined in PRD
        
        Args:
            image_url: URL or base64 of invoice image
            user_id: User ID for context
            business_profile: Optional business profile for personalization
            
        Returns:
            WorkflowResult with all decisions and outcomes
        """
        start_time = datetime.now()
        workflow_id = str(uuid.uuid4())
        decisions = []
        
        logger.info(f"Starting document lifecycle - workflow_id: {workflow_id}")
        
        try:
            # Step 1: Visual Audit (Agent A)
            invoice_data, audit_decision = await self._execute_visual_audit(
                image_url, workflow_id
            )
            decisions.append(audit_decision)
            
            if not invoice_data:
                return WorkflowResult(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.ERROR,
                    invoice_data={},
                    decisions=decisions,
                    requires_review=True,
                    review_reasons=["Visual audit failed"]
                )
            
            # Step 2: Confidence Check
            confidence_decision, requires_review, review_reasons = \
                self._execute_confidence_check(invoice_data)
            decisions.append(confidence_decision)
            
            # Step 3: Proactive Subsidy Check (Agent C auto-trigger)
            subsidy_alerts = []
            subsidy_decision = await self._execute_subsidy_check(
                invoice_data, business_profile or {}
            )
            if subsidy_decision:
                decisions.append(subsidy_decision)
                subsidy_alerts = subsidy_decision.data.get("alerts", [])
            
            # Step 4: Compliance Check (Agent B auto-trigger)
            compliance_alerts = []
            compliance_decision = await self._execute_compliance_check(invoice_data)
            if compliance_decision:
                decisions.append(compliance_decision)
                compliance_alerts = compliance_decision.data.get("alerts", [])
            
            # Step 5: Negotiation Decision
            negotiation_draft = None
            should_negotiate, neg_decision = await self._evaluate_negotiation(
                invoice_data, user_id
            )
            decisions.append(neg_decision)
            
            # Step 6: Draft Negotiation if needed
            if should_negotiate:
                negotiation_draft, draft_decision = await self._execute_negotiation(
                    invoice_data, user_id
                )
                if draft_decision:
                    decisions.append(draft_decision)
            
            # Determine final status
            if negotiation_draft:
                status = WorkflowStatus.WAITING_FOR_APPROVAL
            elif requires_review:
                status = WorkflowStatus.WAITING_FOR_APPROVAL
            else:
                status = WorkflowStatus.COMPLETED
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                invoice_data, subsidy_alerts, compliance_alerts, requires_review
            )
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=status,
                invoice_data=invoice_data,
                decisions=decisions,
                subsidy_alerts=subsidy_alerts,
                compliance_alerts=compliance_alerts,
                negotiation_draft=negotiation_draft,
                requires_review=requires_review,
                review_reasons=review_reasons,
                recommendations=recommendations,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}", exc_info=True)
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.ERROR,
                invoice_data=invoice_data if 'invoice_data' in locals() else {},
                decisions=decisions,
                requires_review=True,
                review_reasons=[f"Workflow error: {str(e)}"]
            )
    
    async def _execute_visual_audit(
        self, 
        image_url: str, 
        workflow_id: str
    ) -> Tuple[Optional[Dict], WorkflowDecision]:
        """Execute Agent A - Visual Auditor"""
        
        try:
            if self.mcp_bridge:
                result = await self.mcp_bridge.call_agent_a(image_url=image_url)
                
                if result.get("success"):
                    invoice_data = result["result"]
                    
                    decision = WorkflowDecision(
                        step=WorkflowStep.VISUAL_AUDIT,
                        decision="success",
                        reason=f"Invoice processed with confidence {invoice_data.get('confidence_score', 0.85):.2f}",
                        triggered_agent="Agent A (Visual Auditor)",
                        data={
                            "vendor": invoice_data.get("vendor_name"),
                            "amount": invoice_data.get("total_amount"),
                            "tampering_detected": invoice_data.get("tampering_detected", False)
                        }
                    )
                    
                    return invoice_data, decision
                else:
                    error = result.get("error", "Unknown error")
                    return None, WorkflowDecision(
                        step=WorkflowStep.VISUAL_AUDIT,
                        decision="failed",
                        reason=f"Visual audit failed: {error}",
                        triggered_agent="Agent A (Visual Auditor)"
                    )
            else:
                # Mock for testing without MCP bridge
                return self._get_mock_invoice_data(), WorkflowDecision(
                    step=WorkflowStep.VISUAL_AUDIT,
                    decision="success",
                    reason="Mock invoice data (MCP bridge not available)",
                    triggered_agent="Agent A (Visual Auditor) - Mock"
                )
                
        except Exception as e:
            logger.error(f"Visual audit error: {e}")
            return None, WorkflowDecision(
                step=WorkflowStep.VISUAL_AUDIT,
                decision="error",
                reason=f"Visual audit exception: {str(e)}",
                triggered_agent="Agent A (Visual Auditor)"
            )
    
    def _execute_confidence_check(
        self, 
        invoice_data: Dict
    ) -> Tuple[WorkflowDecision, bool, List[str]]:
        """Check confidence score and flag for review if needed"""
        
        from confidence_scoring import score_invoice_confidence, CONFIDENCE_THRESHOLD
        
        result = score_invoice_confidence(invoice_data)
        
        requires_review = result.requires_review
        review_reasons = result.review_reasons
        
        decision = WorkflowDecision(
            step=WorkflowStep.CONFIDENCE_CHECK,
            decision="review_required" if requires_review else "auto_approved",
            reason=f"Confidence score: {result.overall_score:.2f} (threshold: {CONFIDENCE_THRESHOLD})",
            data={
                "overall_score": result.overall_score,
                "component_scores": result.component_scores,
                "priority": result.review_priority.value
            }
        )
        
        return decision, requires_review, review_reasons
    
    async def _execute_subsidy_check(
        self, 
        invoice_data: Dict,
        business_profile: Dict
    ) -> Optional[WorkflowDecision]:
        """
        Auto-trigger Agent C for capital goods purchases
        PRD: "Auto-trigger Agent C for Capital Goods > ₹1 Lakh"
        """
        
        # Check for capital goods
        line_items = invoice_data.get("line_items", [])
        capital_goods = [
            item for item in line_items 
            if item.get("category") == "Capital Goods"
        ]
        
        if not capital_goods:
            return None
        
        total_capex = sum(item.get("amount", 0) for item in capital_goods)
        
        # PRD threshold: ₹1 Lakh
        if total_capex < CAPITAL_GOODS_THRESHOLD:
            return WorkflowDecision(
                step=WorkflowStep.SUBSIDY_CHECK,
                decision="skipped",
                reason=f"Capital goods amount (₹{total_capex:,.0f}) below threshold (₹{CAPITAL_GOODS_THRESHOLD:,.0f})"
            )
        
        logger.info(f"🎯 Auto-triggering Agent C for capital goods: ₹{total_capex:,.0f}")
        
        try:
            alerts = []
            
            if self.proactive_engine:
                # Use proactive intelligence engine
                alerts = self.proactive_engine.analyze_invoice_for_subsidies(
                    invoice_data=invoice_data,
                    business_profile=business_profile
                )
                alerts = [alert.to_dict() if hasattr(alert, 'to_dict') else alert for alert in alerts]
            elif self.mcp_bridge:
                # Direct Agent C call
                sector = business_profile.get("industry_type", "manufacturing")
                result = await self.mcp_bridge.call_agent_c(
                    sector=sector,
                    capex_amount=total_capex
                )
                if result.get("success"):
                    alerts = [{
                        "type": "subsidy_match",
                        "title": "Subsidy Opportunities Found",
                        "message": result["result"][:500],
                        "priority": "high"
                    }]
            
            return WorkflowDecision(
                step=WorkflowStep.SUBSIDY_CHECK,
                decision="triggered",
                reason=f"Capital goods purchase of ₹{total_capex:,.0f} detected - {len(alerts)} subsidies found",
                triggered_agent="Agent C (Subsidy Hunter)",
                data={
                    "capital_goods_amount": total_capex,
                    "alerts": alerts,
                    "items": [item.get("description") for item in capital_goods[:3]]
                }
            )
            
        except Exception as e:
            logger.warning(f"Subsidy check failed: {e}")
            return WorkflowDecision(
                step=WorkflowStep.SUBSIDY_CHECK,
                decision="error",
                reason=f"Subsidy check failed: {str(e)}"
            )
    
    async def _execute_compliance_check(
        self, 
        invoice_data: Dict
    ) -> Optional[WorkflowDecision]:
        """
        Auto-trigger Agent B for personal/entertainment items
        PRD: "Auto-trigger Agent B for personal/entertainment items"
        """
        
        # Check for personal/entertainment items
        line_items = invoice_data.get("line_items", [])
        personal_items = [
            item for item in line_items 
            if item.get("category") == "Personal/Entertainment"
        ]
        
        if not personal_items:
            return None
        
        logger.info(f"⚖️ Auto-triggering Agent B for {len(personal_items)} personal items")
        
        try:
            alerts = []
            
            if self.mcp_bridge:
                # Query ITC eligibility
                item_desc = personal_items[0].get("description", "personal expense")
                result = await self.mcp_bridge.call_agent_b(
                    query=f"Can I claim Input Tax Credit on {item_desc}?",
                    user_context=""
                )
                
                if result.get("success"):
                    risk_data = result["result"]
                    alerts.append({
                        "type": "compliance_warning",
                        "title": "ITC Eligibility Warning",
                        "message": risk_data.get("compliant_action", ""),
                        "risk_level": risk_data.get("risk_level", "Medium"),
                        "section": risk_data.get("relevant_section", "Section 17(5)")
                    })
            
            return WorkflowDecision(
                step=WorkflowStep.COMPLIANCE_CHECK,
                decision="triggered",
                reason=f"{len(personal_items)} personal/entertainment items detected - ITC blocked under Section 17(5)",
                triggered_agent="Agent B (Legal Sentinel)",
                data={
                    "personal_items": len(personal_items),
                    "alerts": alerts,
                    "items": [item.get("description") for item in personal_items[:3]]
                }
            )
            
        except Exception as e:
            logger.warning(f"Compliance check failed: {e}")
            return WorkflowDecision(
                step=WorkflowStep.COMPLIANCE_CHECK,
                decision="error", 
                reason=f"Compliance check failed: {str(e)}"
            )
    
    async def _evaluate_negotiation(
        self, 
        invoice_data: Dict,
        user_id: str
    ) -> Tuple[bool, WorkflowDecision]:
        """
        Evaluate if negotiation is needed based on vendor profile and amount
        """
        
        vendor_name = invoice_data.get("vendor_name", "")
        total_amount = invoice_data.get("total_amount", 0)
        
        should_negotiate = False
        reason = ""
        
        # Check vendor profile for spending patterns
        vendor_profile = None
        if self.db:
            from models import VendorProfile
            vendor_profile = self.db.query(VendorProfile).filter(
                VendorProfile.name.ilike(f"%{vendor_name}%")
            ).first()
        
        if vendor_profile:
            # Check for spending spike (>20% above average)
            if total_amount > (vendor_profile.average_spend_monthly * 1.2):
                should_negotiate = True
                reason = f"Spending spike detected: ₹{total_amount:,.0f} vs average ₹{vendor_profile.average_spend_monthly:,.0f}"
        elif total_amount > NEGOTIATION_AMOUNT_THRESHOLD:
            # High amount without vendor history
            should_negotiate = True
            reason = f"High value transaction (₹{total_amount:,.0f}) - No vendor profile found"
        
        decision = WorkflowDecision(
            step=WorkflowStep.NEGOTIATION_DECISION,
            decision="negotiate" if should_negotiate else "skip",
            reason=reason if should_negotiate else f"Amount (₹{total_amount:,.0f}) within normal range",
            data={
                "vendor_name": vendor_name,
                "amount": total_amount,
                "has_vendor_profile": vendor_profile is not None
            }
        )
        
        return should_negotiate, decision
    
    async def _execute_negotiation(
        self, 
        invoice_data: Dict,
        user_id: str
    ) -> Tuple[Optional[Dict], Optional[WorkflowDecision]]:
        """
        Execute Agent D for negotiation draft
        PRD CRITICAL: "Draft-only mode - NEVER auto-send"
        """
        
        vendor_name = invoice_data.get("vendor_name", "Vendor")
        amount = invoice_data.get("total_amount", 0)
        invoice_date = invoice_data.get("invoice_date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            if self.mcp_bridge:
                result = await self.mcp_bridge.call_agent_d(
                    counterparty_name=vendor_name,
                    amount=amount,
                    transaction_type="payable",
                    due_date=invoice_date,
                    current_cash_position=1000000,  # Default, should come from user context
                    upcoming_outflows=500000
                )
                
                if result.get("success"):
                    draft = result["result"]
                    
                    return draft, WorkflowDecision(
                        step=WorkflowStep.NEGOTIATION_DRAFT,
                        decision="drafted",
                        reason=f"Negotiation draft created - REQUIRES HUMAN APPROVAL before sending",
                        triggered_agent="Agent D (Negotiator)",
                        data={
                            "intent": draft.get("intent"),
                            "strategy": draft.get("strategy_explanation"),
                            "draft_only": True  # PRD: Never auto-send
                        }
                    )
            
            return None, None
            
        except Exception as e:
            logger.warning(f"Negotiation draft failed: {e}")
            return None, WorkflowDecision(
                step=WorkflowStep.NEGOTIATION_DRAFT,
                decision="error",
                reason=f"Negotiation draft failed: {str(e)}"
            )
    
    def _generate_recommendations(
        self,
        invoice_data: Dict,
        subsidy_alerts: List[Dict],
        compliance_alerts: List[Dict],
        requires_review: bool
    ) -> List[str]:
        """Generate CA-style recommendations"""
        
        recommendations = []
        
        # Review recommendation
        if requires_review:
            recommendations.append(
                "👨‍💼 This invoice requires manual review by a qualified professional"
            )
        
        # Tampering warning
        if invoice_data.get("tampering_detected"):
            recommendations.append(
                "🚨 CRITICAL: Tampering detected - Request original document from vendor"
            )
        
        # Subsidy opportunity
        if subsidy_alerts:
            recommendations.append(
                f"💰 {len(subsidy_alerts)} subsidy opportunities found - Review before payment"
            )
        
        # Compliance warning
        if compliance_alerts:
            recommendations.append(
                "⚠️ ITC eligibility concerns detected - Review Section 17(5) provisions"
            )
        
        # GSTIN warning
        if not invoice_data.get("gstin") and invoice_data.get("tax_amount", 0) > 0:
            recommendations.append(
                "📋 Missing GSTIN - Request from vendor before claiming ITC"
            )
        
        # Stale invoice
        flags = invoice_data.get("compliance_flags", [])
        if any("Stale" in str(flag) for flag in flags):
            recommendations.append(
                "⏰ Invoice age exceeds 30 days - Check ITC claim timeline"
            )
        
        return recommendations
    
    def _get_mock_invoice_data(self) -> Dict:
        """Return mock invoice data for testing"""
        return {
            "vendor_name": "Test Vendor Pvt Ltd",
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "total_amount": 150000.0,
            "tax_amount": 22881.0,
            "gstin": "27AABCU9603R1ZX",
            "is_handwritten": False,
            "tampering_detected": False,
            "confidence_score": 0.92,
            "line_items": [
                {"description": "Industrial Equipment", "amount": 127119.0, "category": "Capital Goods"},
                {"description": "GST @ 18%", "amount": 22881.0, "category": "Service"}
            ],
            "compliance_flags": []
        }


# Global workflow engine instance
_workflow_engine = None


def get_workflow_engine(
    mcp_bridge=None, 
    proactive_engine=None, 
    db_session=None
) -> WorkflowEngine:
    """Get or create workflow engine instance"""
    global _workflow_engine
    
    if _workflow_engine is None or any([mcp_bridge, proactive_engine, db_session]):
        _workflow_engine = WorkflowEngine(
            mcp_bridge=mcp_bridge,
            proactive_engine=proactive_engine,
            db_session=db_session
        )
    
    return _workflow_engine


async def process_invoice(
    image_url: str,
    user_id: str,
    business_profile: Optional[Dict] = None,
    mcp_bridge=None,
    db_session=None
) -> WorkflowResult:
    """
    Convenience function to process an invoice through the complete workflow
    
    Args:
        image_url: Invoice image URL or base64
        user_id: User ID
        business_profile: Optional business profile
        mcp_bridge: Optional MCP bridge instance
        db_session: Optional database session
        
    Returns:
        WorkflowResult with complete processing results
    """
    engine = get_workflow_engine(mcp_bridge=mcp_bridge, db_session=db_session)
    return await engine.process_document_lifecycle(image_url, user_id, business_profile)
