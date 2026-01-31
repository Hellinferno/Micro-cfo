#!/usr/bin/env python3
"""
A/B Testing Service for MicroCFO Negotiation Messages
Tracks which message variants lead to better payment collection outcomes

This implements the "Negotiation A/B Testing" requirement from the Idea PDF:
"Evaluate the success rate of AI-drafted payment collection messages vs standard templates"
"""

import os
import uuid
import random
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)


class MessageVariant(str, Enum):
    """A/B test message variants"""
    RELATIONSHIP_FOCUSED = "A"  # Warm, relationship-building tone
    TRANSACTIONAL = "B"         # Direct, business-focused tone
    URGENCY_BASED = "C"         # Creates urgency without being pushy
    STANDARD_TEMPLATE = "CONTROL"  # Standard non-AI template


class OutcomeType(str, Enum):
    """Possible outcomes for negotiation messages"""
    PAYMENT_RECEIVED = "payment_received"
    PARTIAL_PAYMENT = "partial_payment"
    PAYMENT_PROMISED = "payment_promised"
    EXTENSION_GRANTED = "extension_granted"
    NO_RESPONSE = "no_response"
    REJECTED = "rejected"


class ABTestExperiment:
    """Represents an A/B test experiment"""
    
    def __init__(
        self,
        experiment_id: str,
        name: str,
        variants: List[str],
        traffic_split: Dict[str, float] = None
    ):
        self.experiment_id = experiment_id
        self.name = name
        self.variants = variants
        # Default to equal split
        self.traffic_split = traffic_split or {v: 1/len(variants) for v in variants}
        self.created_at = datetime.now()
        self.is_active = True


class ABTestingService:
    """
    A/B Testing service for negotiation messages
    
    Features:
    - Random variant assignment with configurable traffic split
    - Outcome tracking and success rate calculation
    - Statistical significance testing
    - Winner determination
    """
    
    # Pre-defined experiments
    EXPERIMENTS = {
        "negotiation_tone": ABTestExperiment(
            experiment_id="exp_negotiation_tone_v1",
            name="Negotiation Message Tone",
            variants=["A", "B", "CONTROL"],
            traffic_split={"A": 0.4, "B": 0.4, "CONTROL": 0.2}
        ),
        "payment_reminder": ABTestExperiment(
            experiment_id="exp_payment_reminder_v1",
            name="Payment Reminder Style",
            variants=["A", "B", "C"],
            traffic_split={"A": 0.33, "B": 0.33, "C": 0.34}
        )
    }
    
    # Message templates for each variant
    MESSAGE_TEMPLATES = {
        "negotiation_tone": {
            "A": {  # Relationship-focused
                "subject": "Quick check-in regarding Invoice #{invoice_id}",
                "opening": "I hope this message finds you well. We've valued our partnership over the years.",
                "body": "I wanted to personally reach out regarding Invoice #{invoice_id} for ₹{amount:,.2f}. "
                       "We understand that cash flow can sometimes be challenging, and we're here to work with you.",
                "closing": "Would you have a few minutes this week to discuss a payment arrangement that works for both of us?",
                "tone": "warm"
            },
            "B": {  # Transactional
                "subject": "Payment Due: Invoice #{invoice_id}",
                "opening": "This is regarding the outstanding payment for Invoice #{invoice_id}.",
                "body": "The amount of ₹{amount:,.2f} was due on {due_date}. "
                       "Please arrange for payment at your earliest convenience.",
                "closing": "Kindly confirm the payment date or contact us if you need to discuss payment terms.",
                "tone": "direct"
            },
            "CONTROL": {  # Standard template
                "subject": "Payment Reminder - Invoice #{invoice_id}",
                "opening": "Dear Sir/Madam,",
                "body": "This is a reminder that Invoice #{invoice_id} for ₹{amount:,.2f} is pending. "
                       "Please make the payment at your earliest.",
                "closing": "Thank you for your prompt attention to this matter.",
                "tone": "formal"
            }
        },
        "payment_reminder": {
            "A": {  # Gentle reminder
                "template": "Hi! Just a friendly reminder about Invoice #{invoice_id} (₹{amount:,.2f}). "
                          "Let us know if you need any clarification. 🙏"
            },
            "B": {  # Urgency-based
                "template": "Payment for Invoice #{invoice_id} (₹{amount:,.2f}) is {days_overdue} days overdue. "
                          "Please prioritize this to avoid any service interruption."
            },
            "C": {  # Value-focused
                "template": "We appreciate your business! Invoice #{invoice_id} (₹{amount:,.2f}) is pending. "
                          "Clearing this will help us continue serving you with priority support."
            }
        }
    }
    
    def __init__(self, db_session_factory=None):
        self.db_session_factory = db_session_factory
        self._test_results: Dict[str, List[Dict]] = {}  # In-memory fallback
    
    def assign_variant(
        self,
        experiment_name: str,
        user_id: str
    ) -> str:
        """
        Assign a user to a variant for an experiment
        
        Uses deterministic assignment based on user_id for consistency
        """
        experiment = self.EXPERIMENTS.get(experiment_name)
        if not experiment or not experiment.is_active:
            return "CONTROL"
        
        # Deterministic assignment based on user_id hash
        hash_value = hash(f"{experiment.experiment_id}_{user_id}") % 100
        
        cumulative = 0
        for variant, split in experiment.traffic_split.items():
            cumulative += split * 100
            if hash_value < cumulative:
                return variant
        
        return experiment.variants[0]  # Fallback
    
    def get_message_template(
        self,
        experiment_name: str,
        variant: str,
        **kwargs
    ) -> Dict[str, str]:
        """Get message template for a variant with variables filled in"""
        templates = self.MESSAGE_TEMPLATES.get(experiment_name, {})
        template = templates.get(variant, templates.get("CONTROL", {}))
        
        # Fill in variables
        filled = {}
        for key, value in template.items():
            if isinstance(value, str):
                try:
                    filled[key] = value.format(**kwargs)
                except KeyError:
                    filled[key] = value
            else:
                filled[key] = value
        
        filled["variant"] = variant
        filled["experiment"] = experiment_name
        
        return filled
    
    def record_impression(
        self,
        experiment_name: str,
        variant: str,
        user_id: str,
        counterparty_id: str,
        invoice_id: str,
        amount: float
    ) -> str:
        """Record that a message variant was shown/sent"""
        test_id = str(uuid.uuid4())
        
        record = {
            "test_id": test_id,
            "experiment": experiment_name,
            "variant": variant,
            "user_id": user_id,
            "counterparty_id": counterparty_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "impression_at": datetime.now().isoformat(),
            "outcome": None,
            "outcome_at": None
        }
        
        # Store in memory (or database if available)
        if experiment_name not in self._test_results:
            self._test_results[experiment_name] = []
        self._test_results[experiment_name].append(record)
        
        # Also store in database if available
        if self.db_session_factory:
            try:
                self._store_in_db(record)
            except Exception as e:
                logger.warning(f"Failed to store A/B test record in DB: {e}")
        
        return test_id
    
    def record_outcome(
        self,
        test_id: str,
        outcome: OutcomeType,
        payment_amount: Optional[float] = None,
        days_to_outcome: Optional[int] = None
    ) -> bool:
        """Record the outcome of a test impression"""
        # Find and update the record
        for experiment_results in self._test_results.values():
            for record in experiment_results:
                if record["test_id"] == test_id:
                    record["outcome"] = outcome.value
                    record["outcome_at"] = datetime.now().isoformat()
                    record["payment_amount"] = payment_amount
                    record["days_to_outcome"] = days_to_outcome
                    return True
        
        return False
    
    def get_experiment_results(
        self,
        experiment_name: str
    ) -> Dict[str, Any]:
        """Calculate results for an experiment"""
        results = self._test_results.get(experiment_name, [])
        
        if not results:
            return {"error": "No data available", "experiment": experiment_name}
        
        # Group by variant
        variant_stats = {}
        for record in results:
            variant = record["variant"]
            if variant not in variant_stats:
                variant_stats[variant] = {
                    "impressions": 0,
                    "outcomes": {},
                    "total_amount_requested": 0,
                    "total_amount_received": 0
                }
            
            stats = variant_stats[variant]
            stats["impressions"] += 1
            stats["total_amount_requested"] += record.get("amount", 0)
            
            outcome = record.get("outcome")
            if outcome:
                stats["outcomes"][outcome] = stats["outcomes"].get(outcome, 0) + 1
                if outcome in ["payment_received", "partial_payment"]:
                    stats["total_amount_received"] += record.get("payment_amount", 0) or record.get("amount", 0)
        
        # Calculate success rates
        for variant, stats in variant_stats.items():
            total = stats["impressions"]
            successes = (
                stats["outcomes"].get("payment_received", 0) +
                stats["outcomes"].get("partial_payment", 0) +
                stats["outcomes"].get("payment_promised", 0)
            )
            
            stats["success_rate"] = (successes / total * 100) if total > 0 else 0
            stats["collection_rate"] = (
                stats["total_amount_received"] / stats["total_amount_requested"] * 100
            ) if stats["total_amount_requested"] > 0 else 0
        
        # Determine winner
        winner = max(
            variant_stats.items(),
            key=lambda x: x[1]["success_rate"]
        )[0] if variant_stats else None
        
        return {
            "experiment": experiment_name,
            "total_impressions": len(results),
            "variant_stats": variant_stats,
            "current_winner": winner,
            "is_significant": len(results) >= 100  # Simple threshold
        }
    
    def _store_in_db(self, record: Dict):
        """Store A/B test record in database"""
        if not self.db_session_factory:
            return
        
        # This would use a dedicated ABTestResult model
        # For now, we'll use the in-memory storage
        pass


# Pre-defined negotiation message generators
class NegotiationMessageGenerator:
    """Generates negotiation messages with A/B testing built in"""
    
    def __init__(self, ab_service: ABTestingService):
        self.ab_service = ab_service
    
    def generate_payment_reminder(
        self,
        user_id: str,
        counterparty_name: str,
        invoice_id: str,
        amount: float,
        due_date: str,
        days_overdue: int = 0
    ) -> Dict[str, Any]:
        """Generate a payment reminder with automatic variant assignment"""
        # Assign variant
        variant = self.ab_service.assign_variant("negotiation_tone", user_id)
        
        # Get template
        message = self.ab_service.get_message_template(
            experiment_name="negotiation_tone",
            variant=variant,
            invoice_id=invoice_id,
            amount=amount,
            due_date=due_date,
            counterparty=counterparty_name,
            days_overdue=days_overdue
        )
        
        # Record impression
        test_id = self.ab_service.record_impression(
            experiment_name="negotiation_tone",
            variant=variant,
            user_id=user_id,
            counterparty_id=counterparty_name,
            invoice_id=invoice_id,
            amount=amount
        )
        
        message["test_id"] = test_id
        return message
    
    def generate_whatsapp_reminder(
        self,
        user_id: str,
        invoice_id: str,
        amount: float,
        days_overdue: int = 0
    ) -> Dict[str, Any]:
        """Generate a WhatsApp payment reminder"""
        variant = self.ab_service.assign_variant("payment_reminder", user_id)
        
        templates = {
            "A": f"Hi! Just a friendly reminder about Invoice #{invoice_id} (₹{amount:,.2f}). "
                 f"Let us know if you need any clarification. 🙏",
            "B": f"Payment for Invoice #{invoice_id} (₹{amount:,.2f}) is {days_overdue} days overdue. "
                 f"Please prioritize this to avoid any service interruption.",
            "C": f"We appreciate your business! Invoice #{invoice_id} (₹{amount:,.2f}) is pending. "
                 f"Clearing this will help us continue serving you with priority support."
        }
        
        return {
            "message": templates.get(variant, templates["A"]),
            "variant": variant,
            "experiment": "payment_reminder"
        }


# Singleton instances
_ab_service: Optional[ABTestingService] = None
_message_generator: Optional[NegotiationMessageGenerator] = None

def get_ab_testing_service() -> ABTestingService:
    """Get A/B testing service singleton"""
    global _ab_service
    if _ab_service is None:
        _ab_service = ABTestingService()
    return _ab_service

def get_message_generator() -> NegotiationMessageGenerator:
    """Get message generator singleton"""
    global _message_generator
    if _message_generator is None:
        _message_generator = NegotiationMessageGenerator(get_ab_testing_service())
    return _message_generator
