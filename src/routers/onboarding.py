#!/usr/bin/env python3
"""
Onboarding Router for MicroCFO Integration Server
Handles user onboarding and company setup flow
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from datetime import datetime

from src.user_onboarding import (
    CompanyProfile,
    OnboardingProgress,
    OnboardingStep,
    IndustryType,
    TurnoverTier,
    GSTRegistrationType,
    IndustryInfo,
    TurnoverInfo,
    OnboardingManager
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# Request/Response Models
class StartOnboardingResponse(BaseModel):
    """Response for starting onboarding"""
    success: bool
    message: str
    session_id: str
    current_step: str
    step_info: Dict[str, Any]


class StepDataRequest(BaseModel):
    """Request for submitting step data"""
    step: str
    data: Dict[str, Any]


class StepDataResponse(BaseModel):
    """Response for step data submission"""
    success: bool
    message: str
    current_step: str
    next_step: Optional[str]
    validation_errors: Optional[List[str]] = None


class OnboardingStatusResponse(BaseModel):
    """Response for onboarding status"""
    user_id: str
    current_step: str
    completed_steps: List[str]
    progress_percentage: int
    company_profile: Optional[CompanyProfile] = None


class IndustryOptionResponse(BaseModel):
    """Response model for industry option"""
    value: str
    label: str
    description: str
    compliance: List[str]
    subsidies: List[str]


class TurnoverOptionResponse(BaseModel):
    """Response model for turnover tier option"""
    value: str
    label: str
    range: str
    description: str
    compliance_level: str
    benefits: List[str]


@router.post("/start", response_model=StartOnboardingResponse)
async def start_onboarding(request: Request):
    """
    Start onboarding process for new user
    
    Creates a new onboarding session and returns the first step information.
    
    Returns:
        StartOnboardingResponse with session details
    
    Requirements: Phase 4 - User Onboarding Flow
    """
    try:
        # Get user context from request
        user_context = getattr(request.state, "user", None)
        user_id = user_context.user_id if user_context else "anonymous"
        
        logger.info(f"Starting onboarding for user {user_id}")
        
        # Create onboarding session
        progress = OnboardingManager.create_onboarding_session(user_id)
        
        # Get first step info
        step_info = OnboardingManager.get_step_info(OnboardingStep.WELCOME)
        
        return StartOnboardingResponse(
            success=True,
            message="Onboarding session created successfully",
            session_id=user_id,  # In production, generate unique session ID
            current_step=progress.current_step.value,
            step_info=step_info
        )
        
    except Exception as e:
        logger.error(f"Failed to start onboarding: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start onboarding: {str(e)}"
        )


@router.post("/step", response_model=StepDataResponse)
async def submit_step_data(request: Request, step_request: StepDataRequest):
    """
    Submit data for current onboarding step
    
    Validates and saves data for the current step, then advances to next step.
    
    Args:
        step_request: Step data including step name and field values
    
    Returns:
        StepDataResponse with validation results and next step
    """
    try:
        # Get user context
        user_context = getattr(request.state, "user", None)
        user_id = user_context.user_id if user_context else "anonymous"
        
        logger.info(f"Processing step {step_request.step} for user {user_id}")
        
        # Validate step
        try:
            current_step = OnboardingStep(step_request.step)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid step: {step_request.step}"
            )
        
        # Validate step data
        is_valid, error_message = OnboardingManager.validate_step_data(
            current_step,
            step_request.data
        )
        
        if not is_valid:
            return StepDataResponse(
                success=False,
                message="Validation failed",
                current_step=current_step.value,
                next_step=None,
                validation_errors=[error_message]
            )
        
        # Get next step
        step_info = OnboardingManager.get_step_info(current_step)
        next_step = step_info.get("next_step")
        
        # TODO: Save step data to database
        
        logger.info(f"Step {current_step.value} completed for user {user_id}")
        
        return StepDataResponse(
            success=True,
            message="Step completed successfully",
            current_step=current_step.value,
            next_step=next_step.value if next_step else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process step: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process step: {str(e)}"
        )


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(request: Request):
    """
    Get current onboarding status for user
    
    Returns the user's current progress through the onboarding flow.
    
    Returns:
        OnboardingStatusResponse with current status
    """
    try:
        # Get user context
        user_context = getattr(request.state, "user", None)
        user_id = user_context.user_id if user_context else "anonymous"
        
        # TODO: Fetch from database
        # For now, return sample data
        total_steps = len(OnboardingStep)
        completed_steps = 3
        progress_percentage = int((completed_steps / total_steps) * 100)
        
        return OnboardingStatusResponse(
            user_id=user_id,
            current_step=OnboardingStep.TURNOVER_SELECTION.value,
            completed_steps=[
                OnboardingStep.WELCOME.value,
                OnboardingStep.COMPANY_BASIC.value,
                OnboardingStep.INDUSTRY_SELECTION.value
            ],
            progress_percentage=progress_percentage,
            company_profile=None
        )
        
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/industries", response_model=List[IndustryOptionResponse])
async def get_industries():
    """
    Get list of available industries for selection
    
    Returns all available industry types with descriptions, typical compliance
    requirements, and available subsidies.
    
    Returns:
        List of industry options
    """
    try:
        industries = IndustryInfo.get_all_industries()
        
        return [
            IndustryOptionResponse(
                value=ind["value"],
                label=ind["label"],
                description=ind["description"],
                compliance=ind["compliance"],
                subsidies=ind["subsidies"]
            )
            for ind in industries
        ]
        
    except Exception as e:
        logger.error(f"Failed to get industries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industries: {str(e)}"
        )


@router.get("/turnover-tiers", response_model=List[TurnoverOptionResponse])
async def get_turnover_tiers():
    """
    Get list of available turnover tiers for selection
    
    Returns all turnover tiers with ranges, compliance levels, and benefits.
    
    Returns:
        List of turnover tier options
    """
    try:
        tiers = TurnoverInfo.get_all_tiers()
        
        return [
            TurnoverOptionResponse(
                value=tier["value"],
                label=tier["label"],
                range=tier["range"],
                description=tier["description"],
                compliance_level=tier["compliance_level"],
                benefits=tier["benefits"]
            )
            for tier in tiers
        ]
        
    except Exception as e:
        logger.error(f"Failed to get turnover tiers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get turnover tiers: {str(e)}"
        )


@router.get("/step/{step}")
async def get_step_info(step: str):
    """
    Get information about specific onboarding step
    
    Args:
        step: Step identifier
    
    Returns:
        Step information dictionary
    """
    try:
        try:
            step_enum = OnboardingStep(step)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step not found: {step}"
            )
        
        step_info = OnboardingManager.get_step_info(step_enum)
        
        return {
            "step": step,
            **step_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get step info: {str(e)}"
        )


@router.post("/complete")
async def complete_onboarding(request: Request, profile: CompanyProfile):
    """
    Complete onboarding process
    
    Finalizes the onboarding with complete company profile.
    
    Args:
        profile: Complete company profile
    
    Returns:
        Success response with profile
    """
    try:
        # Get user context
        user_context = getattr(request.state, "user", None)
        user_id = user_context.user_id if user_context else "anonymous"
        
        logger.info(f"Completing onboarding for user {user_id}")
        
        # Create progress object
        progress = OnboardingProgress(
            user_id=user_id,
            current_step=OnboardingStep.REVIEW,
            completed_steps=[]
        )
        
        # Complete onboarding
        completed_profile = OnboardingManager.complete_onboarding(progress, profile)
        
        # TODO: Save to database
        
        logger.info(f"Onboarding completed for user {user_id}")
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "profile": completed_profile.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )


@router.get("/health")
async def onboarding_health():
    """Health check endpoint for Onboarding router"""
    return {
        "status": "healthy",
        "service": "Onboarding",
        "available_industries": len(IndustryType),
        "available_tiers": len(TurnoverTier),
        "timestamp": datetime.now().isoformat()
    }
