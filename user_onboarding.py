#!/usr/bin/env python3
"""
User Onboarding System for MicroCFO
Handles company setup flow with industry and turnover tier selection
"""

import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class IndustryType(str, Enum):
    """Industry types for business classification"""
    TEXTILE = "textile"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    TRADING = "trading"
    SERVICES = "services"
    RETAIL = "retail"
    CONSTRUCTION = "construction"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    HOSPITALITY = "hospitality"
    AGRICULTURE = "agriculture"
    OTHER = "other"


class TurnoverTier(str, Enum):
    """Turnover tiers for compliance filtering"""
    MICRO = "micro"  # < 5 Cr
    SMALL = "small"  # 5-20 Cr
    MEDIUM = "medium"  # 20-50 Cr
    LARGE = "large"  # > 50 Cr


class GSTRegistrationType(str, Enum):
    """GST registration types"""
    REGULAR = "regular"
    COMPOSITION = "composition"
    NOT_REGISTERED = "not_registered"


class CompanyProfile(BaseModel):
    """Complete company profile for onboarding"""
    # Basic Information
    company_name: str = Field(..., min_length=2, max_length=255)
    industry_type: IndustryType
    turnover_tier: TurnoverTier
    
    # GST Information
    gst_registration_type: GSTRegistrationType
    gstin: Optional[str] = Field(None, pattern=r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$")
    
    # PAN Information
    pan_number: Optional[str] = Field(None, pattern=r"^[A-Z]{5}\d{4}[A-Z]{1}$")
    
    # Contact Information
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s-]{10,15}$")
    
    # Address
    address_line1: str = Field(..., min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    
    # Business Details
    year_of_incorporation: Optional[int] = Field(None, ge=1900, le=2100)
    number_of_employees: Optional[int] = Field(None, ge=1)
    
    # Preferences
    preferred_language: str = Field(default="en", pattern=r"^(en|hi|ta|te|mr|gu|bn)$")
    enable_legal_alerts: bool = Field(default=True)
    enable_subsidy_alerts: bool = Field(default=True)
    
    # Metadata
    onboarding_completed: bool = Field(default=False)
    onboarding_date: Optional[datetime] = None
    
    @validator('gstin')
    def validate_gstin(cls, v, values):
        """Validate GSTIN if GST registered"""
        if values.get('gst_registration_type') == GSTRegistrationType.REGULAR:
            if not v:
                raise ValueError('GSTIN is required for regular GST registration')
        return v
    
    @validator('turnover_tier')
    def validate_turnover_tier(cls, v, values):
        """Validate turnover tier consistency"""
        gst_type = values.get('gst_registration_type')
        if gst_type == GSTRegistrationType.COMPOSITION and v in [TurnoverTier.LARGE]:
            raise ValueError('Composition scheme not available for large turnover')
        return v


class OnboardingStep(str, Enum):
    """Onboarding flow steps"""
    WELCOME = "welcome"
    COMPANY_BASIC = "company_basic"
    INDUSTRY_SELECTION = "industry_selection"
    TURNOVER_SELECTION = "turnover_selection"
    GST_DETAILS = "gst_details"
    CONTACT_DETAILS = "contact_details"
    PREFERENCES = "preferences"
    REVIEW = "review"
    COMPLETE = "complete"


class OnboardingProgress(BaseModel):
    """Track user's onboarding progress"""
    user_id: str
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep] = []
    company_profile: Optional[CompanyProfile] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class IndustryInfo:
    """Information about industries for user selection"""
    
    INDUSTRY_DETAILS = {
        IndustryType.TEXTILE: {
            "name": "Textile & Apparel",
            "description": "Textile manufacturing, garment production, fabric trading",
            "common_compliance": ["GST", "Factory Act", "EPF", "ESI"],
            "typical_subsidies": ["PLI Scheme", "TUFS", "Export incentives"]
        },
        IndustryType.MANUFACTURING: {
            "name": "Manufacturing",
            "description": "General manufacturing, production, assembly",
            "common_compliance": ["GST", "Factory Act", "EPF", "ESI", "Pollution Control"],
            "typical_subsidies": ["PLI Scheme", "MSME subsidies", "Technology upgradation"]
        },
        IndustryType.TECHNOLOGY: {
            "name": "Technology & IT",
            "description": "Software development, IT services, tech products",
            "common_compliance": ["GST", "Income Tax", "EPF", "ESI"],
            "typical_subsidies": ["Startup India", "STPI benefits", "R&D incentives"]
        },
        IndustryType.TRADING: {
            "name": "Trading & Distribution",
            "description": "Wholesale, retail, distribution",
            "common_compliance": ["GST", "Shops & Establishments Act"],
            "typical_subsidies": ["MSME schemes", "Export incentives"]
        },
        IndustryType.SERVICES: {
            "name": "Professional Services",
            "description": "Consulting, professional services, B2B services",
            "common_compliance": ["GST", "Income Tax", "Professional Tax"],
            "typical_subsidies": ["Startup India", "Service export schemes"]
        },
        IndustryType.RETAIL: {
            "name": "Retail",
            "description": "Retail stores, e-commerce, consumer goods",
            "common_compliance": ["GST", "Shops & Establishments Act", "FSSAI (if food)"],
            "typical_subsidies": ["MSME schemes", "Digital payment incentives"]
        },
        IndustryType.CONSTRUCTION: {
            "name": "Construction & Real Estate",
            "description": "Construction, real estate development, infrastructure",
            "common_compliance": ["GST", "RERA", "EPF", "ESI", "Building permits"],
            "typical_subsidies": ["PMAY", "Smart Cities", "Infrastructure schemes"]
        },
        IndustryType.HEALTHCARE: {
            "name": "Healthcare & Pharma",
            "description": "Hospitals, clinics, pharmaceutical, medical devices",
            "common_compliance": ["GST", "Drug License", "Medical Council", "Bio-medical waste"],
            "typical_subsidies": ["Ayushman Bharat", "PLI Pharma", "Medical device schemes"]
        },
        IndustryType.EDUCATION: {
            "name": "Education & Training",
            "description": "Schools, colleges, training institutes, ed-tech",
            "common_compliance": ["GST exemptions", "UGC/AICTE", "RTE Act"],
            "typical_subsidies": ["Skill India", "Digital education schemes"]
        },
        IndustryType.HOSPITALITY: {
            "name": "Hospitality & Tourism",
            "description": "Hotels, restaurants, travel, tourism",
            "common_compliance": ["GST", "FSSAI", "Tourism licenses", "Fire safety"],
            "typical_subsidies": ["Tourism promotion", "MSME schemes"]
        },
        IndustryType.AGRICULTURE: {
            "name": "Agriculture & Agri-business",
            "description": "Farming, agri-processing, agri-tech",
            "common_compliance": ["GST exemptions", "APMC", "Organic certification"],
            "typical_subsidies": ["PM-KISAN", "Agri infrastructure", "FPO schemes"]
        },
        IndustryType.OTHER: {
            "name": "Other",
            "description": "Other industries not listed above",
            "common_compliance": ["GST", "Income Tax"],
            "typical_subsidies": ["MSME schemes"]
        }
    }
    
    @staticmethod
    def get_industry_info(industry: IndustryType) -> Dict[str, Any]:
        """Get detailed information about an industry"""
        return IndustryInfo.INDUSTRY_DETAILS.get(industry, {})
    
    @staticmethod
    def get_all_industries() -> List[Dict[str, Any]]:
        """Get list of all industries with details"""
        return [
            {
                "value": industry.value,
                "label": info["name"],
                "description": info["description"],
                "compliance": info["common_compliance"],
                "subsidies": info["typical_subsidies"]
            }
            for industry, info in IndustryInfo.INDUSTRY_DETAILS.items()
        ]


class TurnoverInfo:
    """Information about turnover tiers"""
    
    TURNOVER_DETAILS = {
        TurnoverTier.MICRO: {
            "name": "Micro (< ₹5 Crore)",
            "range": "Up to ₹5 Crore annual turnover",
            "description": "Small businesses and startups",
            "compliance_level": "Basic",
            "gst_options": ["Regular", "Composition", "Not Registered"],
            "typical_benefits": [
                "Composition scheme eligible",
                "Simplified compliance",
                "MSME benefits",
                "Priority sector lending"
            ]
        },
        TurnoverTier.SMALL: {
            "name": "Small (₹5-20 Crore)",
            "range": "₹5 Crore to ₹20 Crore annual turnover",
            "description": "Growing businesses",
            "compliance_level": "Moderate",
            "gst_options": ["Regular"],
            "typical_benefits": [
                "MSME benefits",
                "Export incentives",
                "Technology upgradation schemes",
                "Credit guarantee schemes"
            ]
        },
        TurnoverTier.MEDIUM: {
            "name": "Medium (₹20-50 Crore)",
            "range": "₹20 Crore to ₹50 Crore annual turnover",
            "description": "Established businesses",
            "compliance_level": "Comprehensive",
            "gst_options": ["Regular"],
            "typical_benefits": [
                "MSME benefits (up to ₹50 Cr)",
                "Export incentives",
                "PLI schemes",
                "Industry-specific subsidies"
            ]
        },
        TurnoverTier.LARGE: {
            "name": "Large (> ₹50 Crore)",
            "range": "Above ₹50 Crore annual turnover",
            "description": "Large enterprises",
            "compliance_level": "Full",
            "gst_options": ["Regular"],
            "typical_benefits": [
                "PLI schemes",
                "Export incentives",
                "Industry-specific subsidies",
                "R&D incentives"
            ]
        }
    }
    
    @staticmethod
    def get_turnover_info(tier: TurnoverTier) -> Dict[str, Any]:
        """Get detailed information about a turnover tier"""
        return TurnoverInfo.TURNOVER_DETAILS.get(tier, {})
    
    @staticmethod
    def get_all_tiers() -> List[Dict[str, Any]]:
        """Get list of all turnover tiers with details"""
        return [
            {
                "value": tier.value,
                "label": info["name"],
                "range": info["range"],
                "description": info["description"],
                "compliance_level": info["compliance_level"],
                "benefits": info["typical_benefits"]
            }
            for tier, info in TurnoverInfo.TURNOVER_DETAILS.items()
        ]


class OnboardingManager:
    """Manager for user onboarding flow"""
    
    @staticmethod
    def create_onboarding_session(user_id: str) -> OnboardingProgress:
        """
        Create new onboarding session
        
        Args:
            user_id: User identifier
            
        Returns:
            OnboardingProgress instance
        """
        progress = OnboardingProgress(
            user_id=user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[]
        )
        logger.info(f"Created onboarding session for user {user_id}")
        return progress
    
    @staticmethod
    def get_step_info(step: OnboardingStep) -> Dict[str, Any]:
        """
        Get information about onboarding step
        
        Args:
            step: Onboarding step
            
        Returns:
            Dictionary with step information
        """
        step_info = {
            OnboardingStep.WELCOME: {
                "title": "Welcome to MicroCFO",
                "description": "Let's set up your company profile",
                "fields": [],
                "next_step": OnboardingStep.COMPANY_BASIC
            },
            OnboardingStep.COMPANY_BASIC: {
                "title": "Company Information",
                "description": "Tell us about your company",
                "fields": ["company_name", "email", "phone"],
                "next_step": OnboardingStep.INDUSTRY_SELECTION
            },
            OnboardingStep.INDUSTRY_SELECTION: {
                "title": "Select Your Industry",
                "description": "This helps us provide relevant compliance and subsidy information",
                "fields": ["industry_type"],
                "options": IndustryInfo.get_all_industries(),
                "next_step": OnboardingStep.TURNOVER_SELECTION
            },
            OnboardingStep.TURNOVER_SELECTION: {
                "title": "Select Your Turnover Tier",
                "description": "This determines applicable compliance requirements",
                "fields": ["turnover_tier"],
                "options": TurnoverInfo.get_all_tiers(),
                "next_step": OnboardingStep.GST_DETAILS
            },
            OnboardingStep.GST_DETAILS: {
                "title": "GST Registration Details",
                "description": "Provide your GST information",
                "fields": ["gst_registration_type", "gstin", "pan_number"],
                "next_step": OnboardingStep.CONTACT_DETAILS
            },
            OnboardingStep.CONTACT_DETAILS: {
                "title": "Contact & Address",
                "description": "Complete your company address",
                "fields": ["address_line1", "address_line2", "city", "state", "pincode"],
                "next_step": OnboardingStep.PREFERENCES
            },
            OnboardingStep.PREFERENCES: {
                "title": "Preferences",
                "description": "Customize your experience",
                "fields": ["preferred_language", "enable_legal_alerts", "enable_subsidy_alerts"],
                "next_step": OnboardingStep.REVIEW
            },
            OnboardingStep.REVIEW: {
                "title": "Review & Confirm",
                "description": "Please review your information",
                "fields": [],
                "next_step": OnboardingStep.COMPLETE
            },
            OnboardingStep.COMPLETE: {
                "title": "Setup Complete!",
                "description": "Your company profile is ready",
                "fields": [],
                "next_step": None
            }
        }
        
        return step_info.get(step, {})
    
    @staticmethod
    def validate_step_data(step: OnboardingStep, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate data for onboarding step
        
        Args:
            step: Current onboarding step
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        step_info = OnboardingManager.get_step_info(step)
        required_fields = step_info.get("fields", [])
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"Field '{field}' is required"
        
        # Step-specific validation
        if step == OnboardingStep.INDUSTRY_SELECTION:
            try:
                IndustryType(data.get("industry_type"))
            except ValueError:
                return False, "Invalid industry type"
        
        elif step == OnboardingStep.TURNOVER_SELECTION:
            try:
                TurnoverTier(data.get("turnover_tier"))
            except ValueError:
                return False, "Invalid turnover tier"
        
        elif step == OnboardingStep.GST_DETAILS:
            gst_type = data.get("gst_registration_type")
            if gst_type == GSTRegistrationType.REGULAR.value:
                if not data.get("gstin"):
                    return False, "GSTIN is required for regular GST registration"
        
        return True, None
    
    @staticmethod
    def complete_onboarding(progress: OnboardingProgress, profile: CompanyProfile) -> CompanyProfile:
        """
        Complete onboarding process
        
        Args:
            progress: Onboarding progress
            profile: Complete company profile
            
        Returns:
            Updated company profile
        """
        profile.onboarding_completed = True
        profile.onboarding_date = datetime.now()
        progress.completed_at = datetime.now()
        progress.current_step = OnboardingStep.COMPLETE
        
        logger.info(f"Completed onboarding for user {progress.user_id}")
        return profile


if __name__ == "__main__":
    # Test onboarding system
    print("="*60)
    print("USER ONBOARDING SYSTEM TEST")
    print("="*60)
    
    # Test industry info
    print("\n1. Available Industries:")
    print("-" * 60)
    industries = IndustryInfo.get_all_industries()
    for ind in industries[:3]:  # Show first 3
        print(f"  - {ind['label']}: {ind['description']}")
    print(f"  ... and {len(industries) - 3} more")
    
    # Test turnover info
    print("\n2. Turnover Tiers:")
    print("-" * 60)
    tiers = TurnoverInfo.get_all_tiers()
    for tier in tiers:
        print(f"  - {tier['label']}: {tier['range']}")
    
    # Test onboarding flow
    print("\n3. Onboarding Flow:")
    print("-" * 60)
    progress = OnboardingManager.create_onboarding_session("user123")
    print(f"  Current step: {progress.current_step.value}")
    
    step_info = OnboardingManager.get_step_info(OnboardingStep.INDUSTRY_SELECTION)
    print(f"  Step title: {step_info['title']}")
    print(f"  Step description: {step_info['description']}")
    
    # Test validation
    print("\n4. Validation Test:")
    print("-" * 60)
    valid, error = OnboardingManager.validate_step_data(
        OnboardingStep.INDUSTRY_SELECTION,
        {"industry_type": "textile"}
    )
    print(f"  Valid: {valid}, Error: {error}")
    
    print("\n✅ Onboarding system tested successfully")
