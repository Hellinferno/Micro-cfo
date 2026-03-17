"""
Agent D: Negotiator - AI-Powered Vendor Negotiation
Generates context-aware negotiation drafts with A/B testing
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum


class NegotiationIntent(str, Enum):
    """Negotiation intent types"""
    CREDIT_EXTENSION = "credit_extension"
    PAYMENT_CHASE = "payment_chase"
    EARLY_PAYMENT_OFFER = "early_payment_offer"


async def generate_negotiation(
    invoice_data: Dict[str, Any],
    negotiation_context: str,
    vendor_relationship: str = "neutral",
    tone: str = "professional",
    generate_variations: bool = True
) -> Dict[str, Any]:
    """
    Generate negotiation email draft
    
    Args:
        invoice_data: Invoice details (vendor, amount, due_date, etc.)
        negotiation_context: Context for negotiation
        vendor_relationship: Relationship status (neutral, good, strained)
        tone: Communication tone (professional, firm, polite, friendly)
        generate_variations: Whether to generate A/B variations
    
    Returns:
        Generated email draft with variations
    """
    try:
        # Determine intent from context
        intent = await determine_negotiation_intent(
            cash_position=0,  # Would come from user context
            upcoming_outflows=0,
            invoice_amount=invoice_data.get("amount", 0),
            due_date=invoice_data.get("due_date", "")
        )
        
        # Generate primary draft
        primary_draft = await _generate_draft(
            invoice_data=invoice_data,
            intent=intent,
            vendor_relationship=vendor_relationship,
            tone=tone,
            variation="primary"
        )
        
        # Generate alternative if requested
        alternative_draft = None
        if generate_variations:
            alternative_draft = await _generate_draft(
                invoice_data=invoice_data,
                intent=intent,
                vendor_relationship=vendor_relationship,
                tone=tone,
                variation="alternative"
            )
        
        # Generate cash flow analysis
        cash_flow_analysis = await _analyze_cash_flow_position(
            invoice_data=invoice_data,
            intent=intent
        )
        
        # Generate recommendations
        recommendations = _get_negotiation_recommendations(intent, vendor_relationship)
        
        return {
            "primary_draft": primary_draft,
            "alternative_draft": alternative_draft,
            "cash_flow_analysis": cash_flow_analysis,
            "recommendations": recommendations
        }
    
    except Exception as e:
        print(f"Error generating negotiation: {e}")
        return _get_mock_negotiation(invoice_data, negotiation_context)


async def _generate_draft(
    invoice_data: Dict[str, Any],
    intent: NegotiationIntent,
    vendor_relationship: str,
    tone: str,
    variation: str = "primary"
) -> Dict[str, Any]:
    """Generate single negotiation draft"""
    
    vendor_name = invoice_data.get("vendor_name", "Vendor")
    invoice_number = invoice_data.get("invoice_number", "INV-XXX")
    amount = invoice_data.get("amount", 0)
    due_date = invoice_data.get("due_date", "")
    
    # Calculate days overdue
    days_overdue = 0
    if due_date:
        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            days_overdue = (datetime.now(due.tzinfo) - due).days
        except:
            pass
    
    # Generate based on intent
    if intent == NegotiationIntent.CREDIT_EXTENSION:
        if variation == "primary":
            # Relationship-focused
            subject = f"Request for Payment Extension - Invoice #{invoice_number}"
            body = f"""Dear {vendor_name},

I hope this email finds you well.

We value our long-standing partnership and appreciate the quality of products/services you've been providing.

I'm writing to request a 15-day extension for Invoice #{invoice_number} (Amount: ₹{amount:,.0f}), currently due on {due_date}.

Due to temporary cash flow timing issues with our receivables, we would greatly appreciate your understanding and support during this period. We remain committed to clearing the payment by the extended date.

Please let me know if this works for you. Happy to discuss if needed.

Thank you for your continued partnership.

Best regards,
[Your Name]
CFO, [Company Name]"""
            
            telegram_message = f"Hi {vendor_name}, need 15 days extension for Invoice #{invoice_number} (₹{amount:,.0f}). Cash flow timing issue. Thanks for understanding! 🙏"
            strategy = "Relationship-focused approach emphasizing partnership and long-term value"
        
        else:
            # Transactional-focused
            subject = f"Payment Extension Request - Invoice #{invoice_number}"
            body = f"""Dear {vendor_name},

Re: Invoice #{invoice_number} | Amount: ₹{amount:,.0f} | Due Date: {due_date}

We request a payment extension of 15 days for the above-referenced invoice.

Reason: Temporary mismatch in receivables collection.

Proposed new payment date: [Date 15 days from original due date]

Please confirm acceptance of this extension request.

Regards,
[Your Name]
Finance Department"""
            
            telegram_message = f"Hi {vendor_name}, requesting 15-day extension for Invoice #{invoice_number}. Payment by [new date]. Confirm please."
            strategy = "Transactional approach with clear terms and dates"
    
    elif intent == NegotiationIntent.PAYMENT_CHASE:
        if variation == "primary":
            # Polite reminder
            subject = f"Gentle Reminder: Invoice #{invoice_number} Overdue by {days_overdue} days"
            body = f"""Dear {vendor_name},

I hope you're doing well.

This is a gentle reminder regarding Invoice #{invoice_number} (Amount: ₹{amount:,.0f}), which was due on {due_date} and is now {days_overdue} days overdue.

We understand that oversights can happen. Could you please provide an update on the payment status?

If there are any issues or clarifications needed from our end, please don't hesitate to reach out.

Looking forward to your prompt response.

Best regards,
[Your Name]
[Company Name]"""
            
            telegram_message = f"Hi {vendor_name}, gentle reminder for Invoice #{invoice_number} (₹{amount:,.0f}), overdue by {days_overdue} days. Please update. Thanks! 😊"
            strategy = "Polite and understanding tone to maintain relationship"
        
        else:
            # Firm reminder
            subject = f"URGENT: Invoice #{invoice_number} Overdue - Immediate Action Required"
            body = f"""Dear {vendor_name},

Invoice #{invoice_number} Details:
- Amount: ₹{amount:,.0f}
- Due Date: {due_date}
- Days Overdue: {days_overdue}

This invoice is now significantly overdue. We request immediate payment or a definitive payment timeline within 48 hours.

Please treat this matter with urgency to avoid any impact on our business relationship.

Regards,
[Your Name]
Finance Department
[Company Name]"""
            
            telegram_message = f"Hi {vendor_name}, Invoice #{invoice_number} (₹{amount:,.0f}) is {days_overdue} days overdue. Need payment or timeline within 48hrs."
            strategy = "Firm tone emphasizing urgency and consequences"
    
    elif intent == NegotiationIntent.EARLY_PAYMENT_OFFER:
        if variation == "primary":
            # Win-win focused
            subject = f"Early Payment Offer - Invoice #{invoice_number}"
            body = f"""Dear {vendor_name},

I hope this email finds you well.

We're in a strong cash position this month and would like to offer early payment for Invoice #{invoice_number} (Amount: ₹{amount:,.0f}, Due: {due_date}).

In exchange for immediate payment, we'd like to request a 2% early payment discount (₹{amount * 0.02:,.0f}).

This would be beneficial for both parties:
- You receive payment {days_until_due(due_date)} days early
- We get a modest discount for early settlement

Please let me know if this interests you. Happy to process payment immediately upon confirmation.

Best regards,
[Your Name]
CFO, [Company Name]"""
            
            telegram_message = f"Hi {vendor_name}, can offer early payment for Invoice #{invoice_number} with 2% discount. Win-win! Let me know 😊"
            strategy = "Win-win framing with mutual benefit"
        
        else:
            # Direct business offer
            subject = f"Early Payment Proposal - Invoice #{invoice_number}"
            body = f"""Dear {vendor_name},

Proposal for Invoice #{invoice_number}:
- Invoice Amount: ₹{amount:,.0f}
- Due Date: {due_date}
- Proposed Payment: Immediate
- Requested Discount: 2% (₹{amount * 0.02:,.0f})

Net Payment on Early Settlement: ₹{amount * 0.98:,.0f}

This offer is valid for acceptance within 48 hours.

Please confirm if you'd like to proceed.

Regards,
[Your Name]
Finance Department"""
            
            telegram_message = f"Hi {vendor_name}, offering immediate payment for Invoice #{invoice_number} at 2% discount. Valid 48hrs. Interested?"
            strategy = "Direct business proposal with clear terms"
    
    else:
        # Generic fallback
        subject = f"Regarding Invoice #{invoice_number}"
        body = f"""Dear {vendor_name},

I hope you're doing well.

I'm writing regarding Invoice #{invoice_number} (Amount: ₹{amount:,.0f}).

{negotiation_context}

Please let me know your thoughts on this matter.

Best regards,
[Your Name]
[Company Name]"""
        
        telegram_message = f"Hi {vendor_name}, regarding Invoice #{invoice_number}. {negotiation_context[:50]}..."
        strategy = "Generic negotiation approach"
    
    return {
        "subject": subject,
        "body": body,
        "telegram_message": telegram_message,
        "strategy_explanation": strategy,
        "intent": intent.value,
        "tone": tone,
        "variation_id": variation
    }


def days_until_due(due_date: str) -> int:
    """Calculate days until due date"""
    try:
        due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        return (due - datetime.now(due.tzinfo)).days
    except:
        return 0


async def determine_negotiation_intent(
    cash_position: float,
    upcoming_outflows: float,
    invoice_amount: float,
    due_date: str
) -> NegotiationIntent:
    """
    Determine negotiation intent based on financial position
    
    Returns:
        Recommended negotiation intent
    """
    # Calculate cash flow status
    projected_balance = cash_position - upcoming_outflows
    
    # Check if invoice is overdue
    is_overdue = False
    if due_date:
        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            is_overdue = datetime.now(due.tzinfo) > due
        except:
            pass
    
    # Determine intent
    if is_overdue:
        return NegotiationIntent.PAYMENT_CHASE
    elif projected_balance < 0 or cash_position < upcoming_outflows * 0.5:
        return NegotiationIntent.CREDIT_EXTENSION
    elif cash_position > upcoming_outflows * 1.5:
        return NegotiationIntent.EARLY_PAYMENT_OFFER
    else:
        return NegotiationIntent.CREDIT_EXTENSION


async def _analyze_cash_flow_position(
    invoice_data: Dict[str, Any],
    intent: NegotiationIntent
) -> Dict[str, Any]:
    """Analyze cash flow position for negotiation context"""
    return {
        "intent": intent.value,
        "cash_flow_status": "tight" if intent == NegotiationIntent.CREDIT_EXTENSION else "healthy",
        "recommendation": f"Recommended strategy: {intent.value.replace('_', ' ')}",
        "timing": "urgent" if intent == NegotiationIntent.PAYMENT_CHASE else "normal"
    }


def _get_negotiation_recommendations(
    intent: NegotiationIntent,
    vendor_relationship: str
) -> List[str]:
    """Get negotiation recommendations"""
    recommendations = []
    
    if intent == NegotiationIntent.CREDIT_EXTENSION:
        recommendations.append("Offer to provide post-dated cheque for assurance")
        recommendations.append("Propose a specific payment date rather than open-ended extension")
        if vendor_relationship == "good":
            recommendations.append("Leverage good relationship - remind them of timely past payments")
    
    elif intent == NegotiationIntent.PAYMENT_CHASE:
        recommendations.append("Start with polite reminder, escalate if no response in 48hrs")
        recommendations.append("Offer to resolve any disputes or issues blocking payment")
        recommendations.append("Consider phone call for faster resolution")
    
    elif intent == NegotiationIntent.EARLY_PAYMENT_OFFER:
        recommendations.append("Start with 2-3% discount offer, negotiate down if needed")
        recommendations.append("Ensure finance team can process payment immediately upon acceptance")
        recommendations.append("Document agreement for future reference")
    
    return recommendations


def _get_mock_negotiation(
    invoice_data: Dict[str, Any],
    negotiation_context: str
) -> Dict[str, Any]:
    """Return mock negotiation for testing"""
    return {
        "primary_draft": {
            "subject": f"Regarding Invoice #{invoice_data.get('invoice_number', 'XXX')}",
            "body": f"Dear {invoice_data.get('vendor_name', 'Vendor')},\n\n{negotiation_context}\n\nBest regards,\n[Your Name]",
            "telegram_message": f"Hi {invoice_data.get('vendor_name', 'Vendor')}, {negotiation_context[:100]}...",
            "strategy_explanation": "Generic negotiation approach",
            "intent": "credit_extension",
            "tone": "professional",
            "variation_id": "primary"
        },
        "alternative_draft": None,
        "cash_flow_analysis": {
            "intent": "credit_extension",
            "cash_flow_status": "unknown",
            "recommendation": "Review cash flow before sending",
            "timing": "normal"
        },
        "recommendations": [
            "Customize the template with specific details",
            "Consider vendor relationship before sending",
            "Follow up if no response within 48 hours"
        ]
    }


def initialize_agent_d():
    """Initialize Agent D (Negotiator)"""
    print("Agent D (Negotiator) initialized")
    return True
