#!/usr/bin/env python3
"""
Subsidy Hunter Router for MicroCFO Integration Server
Handles Agent C (Subsidy Hunter) REST endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from datetime import datetime

from src.mcp_bridge import MCPBridge, MCPBridgeError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agents/subsidy-hunter", tags=["Subsidy Hunter"])

# Request/Response Models
class SubsidySearchRequest(BaseModel):
    """Request model for subsidy discovery"""
    sector: str = Field(..., description="Business sector", min_length=1, max_length=100)
    capex_amount: float = Field(..., description="Capital expenditure amount in rupees", gt=0)
    location: Optional[str] = Field(None, description="Business location for location-specific schemes")
    
    @validator('sector')
    def validate_sector(cls, v):
        """Validate sector input"""
        if not v or not v.strip():
            raise ValueError('Sector cannot be empty')
        return v.strip().lower()
    
    @validator('capex_amount')
    def validate_capex_amount(cls, v):
        """Validate capex amount"""
        if v <= 0:
            raise ValueError('Capital expenditure amount must be greater than 0')
        if v > 10000000000:  # 1000 crores limit
            raise ValueError('Capital expenditure amount exceeds maximum limit')
        return v

class SubsidySearchResponse(BaseModel):
    """Response model for subsidy discovery"""
    subsidy_information: str = Field(..., description="Detailed subsidy information and recommendations")
    processing_time: float = Field(..., description="Processing time in seconds")
    sector_searched: str = Field(..., description="Sector that was searched")
    capex_amount_searched: float = Field(..., description="Capital expenditure amount that was searched")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str

@router.post("/find-subsidies", response_model=SubsidySearchResponse)
async def find_subsidies(request: Request, subsidy_request: SubsidySearchRequest):
    """
    Find applicable subsidies using Agent C (Subsidy Hunter)
    
    This endpoint handles subsidy discovery with:
    - Enhanced scheme-aware subsidy discovery with benefit calculation
    - Sector and capex amount validation
    - Integration with existing find_applicable_subsidies MCP tool
    - Conservative CA-style recommendations
    
    Args:
        subsidy_request: The subsidy search parameters including sector and capex amount
    
    Returns:
        SubsidySearchResponse: Detailed subsidy information and recommendations
    
    Requirements: 1.3
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing subsidy search request - sector: {subsidy_request.sector}, capex: ₹{subsidy_request.capex_amount:,.0f}")
        
        # Get MCP bridge from app state (with safe access)
        mcp_bridge = getattr(request.app.state, 'mcp_bridge', None)
        if not mcp_bridge:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP bridge not initialized. Service temporarily unavailable."
            )
        
        # Call Agent C via MCP bridge
        result = await mcp_bridge.call_agent_c(
            sector=subsidy_request.sector,
            capex_amount=subsidy_request.capex_amount
        )
        
        # Extract the subsidy data from MCP result
        if not result.get("success"):
            error_msg = result.get("error", "MCP tool execution failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP tool execution failed: {error_msg}"
            )
        
        subsidy_information = result["result"]
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create response
        response = SubsidySearchResponse(
            subsidy_information=subsidy_information,
            processing_time=processing_time,
            sector_searched=subsidy_request.sector,
            capex_amount_searched=subsidy_request.capex_amount
        )
        
        logger.info(f"Subsidy search completed successfully in {processing_time:.2f}s for sector: {subsidy_request.sector}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions to avoid being caught by general handler
        raise
    except MCPBridgeError as e:
        logger.error(f"MCP Bridge error in find_subsidies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subsidy search failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in find_subsidies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during subsidy search"
        )

@router.get("/health")
async def subsidy_hunter_health():
    """Health check endpoint for Subsidy Hunter router"""
    return {
        "status": "healthy",
        "agent": "Subsidy Hunter (Agent C)",
        "endpoints": ["/find-subsidies"],
        "timestamp": datetime.now().isoformat()
    }