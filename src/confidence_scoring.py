#!/usr/bin/env python3
"""
Confidence Scoring Module for MicroCFO
Implements PRD requirement: "Confidence threshold 0.7 triggers manual review"

This module provides:
1. Confidence score calculation for AI outputs
2. Automatic flagging when confidence drops below threshold
3. Risk-based categorization for CA-style review
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ReviewPriority(str, Enum):
    """Review priority levels based on confidence and risk"""
    CRITICAL = "critical"      # Immediate CA review required
    HIGH = "high"              # Review within 24 hours
    MEDIUM = "medium"          # Review within 3 days
    LOW = "low"                # Standard review queue
    AUTO_APPROVED = "auto"     # No review needed


@dataclass
class ConfidenceResult:
    """Result of confidence scoring"""
    overall_score: float
    component_scores: Dict[str, float]
    requires_review: bool
    review_priority: ReviewPriority
    review_reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# PRD Requirement: Confidence threshold 0.7 triggers manual review
CONFIDENCE_THRESHOLD = 0.7

# Risk weights for different categories
RISK_WEIGHTS = {
    "tampering_detected": 0.3,      # High weight - fraud indicator
    "handwritten": 0.2,             # Medium weight - OCR reliability
    "missing_gstin": 0.15,          # Medium weight - compliance risk
    "personal_items": 0.15,         # Medium weight - ITC eligibility
    "stale_invoice": 0.1,           # Low weight - timing issue
    "high_amount": 0.1,             # Low weight - materiality
}

# Amount thresholds (in INR)
AMOUNT_THRESHOLDS = {
    "high": 500000,         # ₹5 Lakhs - requires additional scrutiny
    "very_high": 2500000,   # ₹25 Lakhs - requires CA review
    "extreme": 10000000,    # ₹1 Crore - requires senior review
}


class ConfidenceScorer:
    """
    Calculates confidence scores for AI-processed invoices
    Implements CA-style conservative assessment approach
    """
    
    def __init__(self, base_threshold: float = CONFIDENCE_THRESHOLD):
        self.threshold = base_threshold
        logger.info(f"ConfidenceScorer initialized with threshold: {self.threshold}")
    
    def score_invoice(self, invoice_data: Dict[str, Any]) -> ConfidenceResult:
        """
        Calculate confidence score for processed invoice
        
        PRD Requirements:
        - >90% field extraction accuracy
        - >85% tampering detection accuracy
        - Confidence threshold 0.7 triggers manual review
        
        Args:
            invoice_data: Extracted invoice data from Agent A
            
        Returns:
            ConfidenceResult with scoring details and review requirements
        """
        component_scores = {}
        review_reasons = []
        recommendations = []
        
        # 1. Base confidence from AI extraction
        base_confidence = invoice_data.get("confidence_score", 0.85)
        component_scores["ai_extraction"] = base_confidence
        
        # 2. Fraud detection score
        fraud_score = self._calculate_fraud_score(invoice_data, review_reasons)
        component_scores["fraud_detection"] = fraud_score
        
        # 3. Compliance score
        compliance_score = self._calculate_compliance_score(invoice_data, review_reasons)
        component_scores["compliance"] = compliance_score
        
        # 4. Data completeness score
        completeness_score = self._calculate_completeness_score(invoice_data, review_reasons)
        component_scores["completeness"] = completeness_score
        
        # 5. Amount risk score
        amount_score = self._calculate_amount_score(invoice_data, review_reasons)
        component_scores["amount_risk"] = amount_score
        
        # Calculate weighted overall score
        weights = {
            "ai_extraction": 0.3,
            "fraud_detection": 0.25,
            "compliance": 0.2,
            "completeness": 0.15,
            "amount_risk": 0.1
        }
        
        overall_score = sum(
            component_scores[key] * weights[key]
            for key in weights
        )
        
        # Determine if review is required (PRD threshold: 0.7)
        requires_review = overall_score < self.threshold
        
        # Determine review priority
        review_priority = self._determine_review_priority(
            overall_score, 
            invoice_data, 
            review_reasons
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score,
            component_scores,
            invoice_data
        )
        
        return ConfidenceResult(
            overall_score=round(overall_score, 3),
            component_scores={k: round(v, 3) for k, v in component_scores.items()},
            requires_review=requires_review,
            review_priority=review_priority,
            review_reasons=review_reasons,
            recommendations=recommendations,
            metadata={
                "threshold_used": self.threshold,
                "total_amount": invoice_data.get("total_amount", 0),
                "vendor": invoice_data.get("vendor_name", "Unknown")
            }
        )
    
    def _calculate_fraud_score(
        self, 
        invoice_data: Dict[str, Any], 
        review_reasons: List[str]
    ) -> float:
        """Calculate fraud detection confidence score"""
        score = 1.0
        
        # Tampering detected - major red flag
        if invoice_data.get("tampering_detected", False):
            score -= 0.4
            review_reasons.append("⚠️ TAMPERING DETECTED - Manual verification required")
        
        # Handwritten invoice - lower OCR reliability
        if invoice_data.get("is_handwritten", False):
            score -= 0.2
            review_reasons.append("Handwritten invoice - Verify amounts manually")
        
        # Low AI confidence on extraction
        if invoice_data.get("confidence_score", 1.0) < 0.7:
            score -= 0.2
            review_reasons.append("Low AI confidence on data extraction")
        
        return max(0.0, score)
    
    def _calculate_compliance_score(
        self, 
        invoice_data: Dict[str, Any], 
        review_reasons: List[str]
    ) -> float:
        """Calculate compliance confidence score"""
        score = 1.0
        flags = invoice_data.get("compliance_flags", [])
        
        # Missing GSTIN with tax charged
        if not invoice_data.get("gstin") and invoice_data.get("tax_amount", 0) > 0:
            score -= 0.3
            review_reasons.append("Missing GSTIN - Tax charged without valid GST number")
        
        # Personal/entertainment items (Section 17(5) ITC blocked)
        line_items = invoice_data.get("line_items", [])
        personal_items = [
            item for item in line_items 
            if item.get("category") == "Personal/Entertainment"
        ]
        if personal_items:
            score -= 0.2 * len(personal_items) / max(len(line_items), 1)
            review_reasons.append(f"{len(personal_items)} personal/entertainment items - ITC blocked under Section 17(5)")
        
        # Stale invoice (>30 days old)
        if any("Stale" in str(flag) for flag in flags):
            score -= 0.15
            review_reasons.append("Stale invoice - ITC claim may be rejected")
        
        return max(0.0, score)
    
    def _calculate_completeness_score(
        self, 
        invoice_data: Dict[str, Any], 
        review_reasons: List[str]
    ) -> float:
        """Calculate data completeness score"""
        score = 1.0
        
        # Required fields
        required_fields = ["vendor_name", "invoice_date", "total_amount"]
        missing_fields = [f for f in required_fields if not invoice_data.get(f)]
        
        if missing_fields:
            score -= 0.3 * len(missing_fields) / len(required_fields)
            review_reasons.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Important but not critical fields
        important_fields = ["tax_amount", "gstin", "line_items"]
        missing_important = [f for f in important_fields if not invoice_data.get(f)]
        
        if missing_important:
            score -= 0.15 * len(missing_important) / len(important_fields)
        
        # Check line items quality
        line_items = invoice_data.get("line_items", [])
        if line_items:
            items_with_category = [
                item for item in line_items 
                if item.get("category") and item.get("amount")
            ]
            category_completeness = len(items_with_category) / len(line_items)
            if category_completeness < 0.8:
                score -= 0.1
                review_reasons.append("Some line items missing category or amount")
        
        return max(0.0, score)
    
    def _calculate_amount_score(
        self, 
        invoice_data: Dict[str, Any], 
        review_reasons: List[str]
    ) -> float:
        """Calculate amount-based risk score"""
        score = 1.0
        total_amount = invoice_data.get("total_amount", 0)
        
        if total_amount >= AMOUNT_THRESHOLDS["extreme"]:
            score -= 0.4
            review_reasons.append(f"Extreme value invoice (₹{total_amount:,.0f}) - Senior review required")
        elif total_amount >= AMOUNT_THRESHOLDS["very_high"]:
            score -= 0.25
            review_reasons.append(f"Very high value invoice (₹{total_amount:,.0f}) - CA review recommended")
        elif total_amount >= AMOUNT_THRESHOLDS["high"]:
            score -= 0.1
            review_reasons.append(f"High value invoice (₹{total_amount:,.0f}) - Additional scrutiny")
        
        return max(0.0, score)
    
    def _determine_review_priority(
        self,
        overall_score: float,
        invoice_data: Dict[str, Any],
        review_reasons: List[str]
    ) -> ReviewPriority:
        """Determine review priority based on score and risk factors"""
        
        # Critical - tampering or very low confidence
        if invoice_data.get("tampering_detected") or overall_score < 0.4:
            return ReviewPriority.CRITICAL
        
        # High - fraud indicators or high-value with low confidence
        if overall_score < 0.5:
            return ReviewPriority.HIGH
        
        total_amount = invoice_data.get("total_amount", 0)
        if total_amount >= AMOUNT_THRESHOLDS["very_high"] and overall_score < 0.7:
            return ReviewPriority.HIGH
        
        # Medium - below threshold but no critical issues
        if overall_score < self.threshold:
            return ReviewPriority.MEDIUM
        
        # Low - minor issues
        if review_reasons:
            return ReviewPriority.LOW
        
        # Auto-approved
        return ReviewPriority.AUTO_APPROVED
    
    def _generate_recommendations(
        self,
        overall_score: float,
        component_scores: Dict[str, float],
        invoice_data: Dict[str, Any]
    ) -> List[str]:
        """Generate CA-style recommendations based on analysis"""
        recommendations = []
        
        if component_scores.get("fraud_detection", 1) < 0.7:
            recommendations.append(
                "🔍 Verify source document authenticity - request original invoice"
            )
        
        if component_scores.get("compliance", 1) < 0.8:
            recommendations.append(
                "📋 Review ITC eligibility before claiming - consult GST provisions"
            )
        
        if not invoice_data.get("gstin") and invoice_data.get("tax_amount", 0) > 0:
            recommendations.append(
                "⚠️ Request valid GSTIN from vendor before payment"
            )
        
        if overall_score < self.threshold:
            recommendations.append(
                "👨‍💼 Consult with Chartered Accountant before booking this invoice"
            )
        
        # Capital goods subsidy recommendation
        line_items = invoice_data.get("line_items", [])
        capital_goods = [
            item for item in line_items 
            if item.get("category") == "Capital Goods"
        ]
        if capital_goods:
            total_capex = sum(item.get("amount", 0) for item in capital_goods)
            if total_capex >= 100000:
                recommendations.append(
                    f"💰 Capital goods detected (₹{total_capex:,.0f}) - Check subsidy eligibility"
                )
        
        return recommendations


# Global scorer instance
confidence_scorer = ConfidenceScorer()


def score_invoice_confidence(invoice_data: Dict[str, Any]) -> ConfidenceResult:
    """
    Convenience function to score invoice confidence
    
    Args:
        invoice_data: Extracted invoice data from Agent A
        
    Returns:
        ConfidenceResult with scoring details
    """
    return confidence_scorer.score_invoice(invoice_data)


def requires_manual_review(invoice_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Quick check if invoice requires manual review
    
    Args:
        invoice_data: Extracted invoice data
        
    Returns:
        Tuple of (requires_review: bool, reason: str)
    """
    result = confidence_scorer.score_invoice(invoice_data)
    
    if result.requires_review:
        reason = result.review_reasons[0] if result.review_reasons else "Confidence below threshold"
        return True, reason
    
    return False, "Auto-approved"


def get_review_queue_priority(invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort invoices by review priority for CA dashboard
    
    Args:
        invoices: List of invoice data
        
    Returns:
        Sorted list with scoring metadata
    """
    scored_invoices = []
    
    for invoice in invoices:
        result = confidence_scorer.score_invoice(invoice)
        scored_invoices.append({
            **invoice,
            "_confidence": {
                "score": result.overall_score,
                "priority": result.review_priority.value,
                "reasons": result.review_reasons,
                "recommendations": result.recommendations
            }
        })
    
    # Sort by priority (critical first) then by score (lowest first)
    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "auto": 4
    }
    
    return sorted(
        scored_invoices,
        key=lambda x: (
            priority_order.get(x["_confidence"]["priority"], 5),
            x["_confidence"]["score"]
        )
    )
