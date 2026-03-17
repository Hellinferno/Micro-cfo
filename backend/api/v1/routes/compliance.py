"""
Compliance Query API (Agent B - Legal Sentinel)
Structure-aware RAG for legal compliance checking
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class RiskLevel(str, Enum):
    """Compliance risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceQueryRequest(BaseModel):
    """Compliance query request"""
    query: str
    user_context: Optional[Dict[str, Any]] = None  # turnover, sector, state, etc.


class ComplianceSection(BaseModel):
    """Relevant legal section"""
    section_name: str
    section_number: str
    act_name: str
    description: str
    relevance_score: float


class ComplianceResponse(BaseModel):
    """Compliance query response"""
    risk_level: RiskLevel
    relevant_sections: List[ComplianceSection]
    explanation: str
    compliant_action: str
    warnings: Optional[List[str]] = None
    references: Optional[List[str]] = None


@router.post("/query", response_model=ComplianceResponse)
async def query_compliance(request: ComplianceQueryRequest):
    """
    Query legal compliance using Agent B (Legal Sentinel)
    
    Uses structure-aware RAG to:
    - Search legal database (GST Act, Income Tax, Companies Act)
    - Filter by user context (turnover, sector)
    - Provide CA-style conservative interpretations
    - Reference specific sections with explanations
    """
    try:
        from backend.agents.legal_sentinel import check_compliance_law
        
        # Process query with Legal Sentinel
        result = await check_compliance_law(
            query=request.query,
            user_context=request.user_context
        )
        
        return ComplianceResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process compliance query: {str(e)}"
        )


@router.get("/sections")
async def search_sections(
    query: str,
    act: Optional[str] = None,
    limit: int = 10
):
    """
    Search legal sections by keyword
    
    Returns relevant sections from legal database
    """
    try:
        from backend.agents.legal_sentinel import search_legal_sections
        
        sections = await search_legal_sections(query, act, limit)
        
        return {
            "success": True,
            "data": {
                "sections": sections,
                "total": len(sections)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search sections: {str(e)}"
        )


@router.get("/history")
async def get_query_history(
    skip: int = 0,
    limit: int = 20
):
    """
    Get user's compliance query history
    
    Returns paginated list of previous queries
    """
    # TODO: Implement database query
    return {
        "success": True,
        "data": {
            "queries": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }
    }


@router.post("/monitor/subscribe")
async def subscribe_to_monitoring(
    sectors: List[str],
    acts: Optional[List[str]] = None
):
    """
    Subscribe to legal change monitoring
    
    Agent B will monitor government websites and alert
    user of relevant changes
    """
    # TODO: Implement monitoring subscription
    return {
        "success": True,
        "message": "Monitoring subscription created",
        "data": {
            "sectors": sectors,
            "acts": acts or ["GST", "Income Tax", "Companies Act"]
        }
    }
