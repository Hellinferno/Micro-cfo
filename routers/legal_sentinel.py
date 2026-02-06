#!/usr/bin/env python3
"""
Legal Sentinel Router for MicroCFO Integration Server
Handles Agent B (Legal Sentinel) REST endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field
from datetime import datetime

from mcp_bridge import MCPBridge, MCPBridgeError
from cache_manager import cache_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agents/legal-sentinel", tags=["Legal Sentinel"])

# Request/Response Models
class ComplianceCheckRequest(BaseModel):
    """Request model for legal compliance queries"""
    query: str = Field(..., description="Legal compliance query", min_length=1, max_length=1000)
    user_context: Optional[str] = Field("", description="Additional user context for personalized responses")

class ComplianceCheckResponse(BaseModel):
    """Response model for legal compliance queries"""
    risk_level: str = Field(..., description="Risk level: Low, Medium, or High")
    relevant_section: str = Field(..., description="Relevant legal section or provision")
    compliant_action: str = Field(..., description="Recommended compliant action")
    processing_time: float = Field(..., description="Processing time in seconds")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str

@router.post("/check-compliance", response_model=ComplianceCheckResponse)
async def check_compliance(request: Request, compliance_request: ComplianceCheckRequest):
    """
    Check legal compliance using Agent B (Legal Sentinel)
    
    This endpoint handles legal compliance queries with:
    - Structure-aware RAG system for legal document retrieval
    - User context passing for personalized responses
    - Turnover-based compliance filtering
    - Conservative CA-style legal interpretations
    
    Args:
        compliance_request: The compliance query and optional user context
    
    Returns:
        ComplianceCheckResponse: Risk assessment and recommended actions
    
    Requirements: 1.3, 2.4
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing compliance check request - query: {compliance_request.query[:100]}...")
        
        # Generate cache key based on query and user context
        cache_key = cache_manager.generate_key(
            "legal_query",
            query=compliance_request.query,
            user_context=compliance_request.user_context or ""
        )
        
        # Check cache first
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            logger.info(f"Returning cached compliance check result")
            # Add processing time to cached result
            cached_result["processing_time"] = (datetime.now() - start_time).total_seconds()
            return ComplianceCheckResponse(**cached_result)
        
        # Get MCP bridge from app state (with safe access)
        mcp_bridge = getattr(request.app.state, 'mcp_bridge', None)
        if not mcp_bridge:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP bridge not initialized. Service temporarily unavailable."
            )
        
        # Call Agent B via MCP bridge
        result = await mcp_bridge.call_agent_b(
            query=compliance_request.query,
            user_context=compliance_request.user_context
        )
        
        # Extract the legal risk data from MCP result
        if not result.get("success"):
            error_msg = result.get("error", "MCP tool execution failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP tool execution failed: {error_msg}"
            )
        
        legal_risk_data = result["result"]
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create response
        response = ComplianceCheckResponse(
            risk_level=legal_risk_data["risk_level"],
            relevant_section=legal_risk_data["relevant_section"],
            compliant_action=legal_risk_data["compliant_action"],
            processing_time=processing_time
        )
        
        # Cache the result (without processing_time for consistency)
        cache_data = {
            "risk_level": legal_risk_data["risk_level"],
            "relevant_section": legal_risk_data["relevant_section"],
            "compliant_action": legal_risk_data["compliant_action"]
        }
        cache_manager.set(cache_key, cache_data, ttl=3600)  # Cache for 1 hour
        
        logger.info(f"Compliance check completed successfully in {processing_time:.2f}s - Risk: {legal_risk_data['risk_level']}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions to avoid being caught by general handler
        raise
    except MCPBridgeError as e:
        logger.error(f"MCP Bridge error in check_compliance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Legal compliance check failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in check_compliance: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during compliance check"
        )

@router.get("/health")
async def legal_sentinel_health():
    """Health check endpoint for Legal Sentinel router"""
    return {
        "status": "healthy",
        "agent": "Legal Sentinel (Agent B)",
        "endpoints": ["/check-compliance"],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/invalidate-cache")
async def invalidate_legal_cache():
    """
    Invalidate all cached legal queries
    
    This endpoint allows manual cache invalidation when legal content is updated.
    Useful for ensuring users get the latest legal information after updates.
    
    Returns:
        dict: Number of cache entries invalidated
    
    Requirements: 6.2
    """
    try:
        count = cache_manager.invalidate_prefix("legal_query")
        logger.info(f"Legal query cache invalidated: {count} entries removed")
        
        return {
            "status": "success",
            "message": f"Invalidated {count} cached legal queries",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error invalidating legal cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache"
        )