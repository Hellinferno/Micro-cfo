"""
Subsidy Search API (Agent C - Subsidy Hunter)
Government scheme discovery and matching
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/subsidies", tags=["Subsidies"])


class SubsidySearchRequest(BaseModel):
    """Subsidy search request"""
    sector: Optional[str] = None
    capex: Optional[float] = None
    state: Optional[str] = None
    query: Optional[str] = None


class SubsidyDocument(BaseModel):
    """Required document for subsidy application"""
    name: str
    type: str
    required: bool = True


class SubsidyScheme(BaseModel):
    """Government subsidy scheme"""
    name: str
    benefit: str
    eligibility: str
    ministry: str
    link: Optional[str] = None
    max_subsidy: Optional[str] = None
    match_score: float
    documents_required: List[SubsidyDocument]
    sector_tags: Optional[List[str]] = None
    state_specific: Optional[str] = None


class SubsidySearchResponse(BaseModel):
    """Subsidy search response"""
    schemes: List[SubsidyScheme]
    total_matches: int
    search_context: Dict[str, Any]


@router.post("/search", response_model=SubsidySearchResponse)
async def search_subsidies(request: SubsidySearchRequest):
    """
    Search government subsidies using Agent C (Subsidy Hunter)
    
    Matches schemes based on:
    - Business sector (Textile, Manufacturing, IT, etc.)
    - CAPEX amount (for capital goods subsidies)
    - State location (for state-specific schemes)
    - Natural language query
    """
    try:
        from backend.agents.subsidy_hunter import find_subsidies
        
        # Search for subsidies
        schemes = await find_subsidies(
            sector=request.sector,
            capex=request.capex,
            state=request.state,
            query=request.query
        )
        
        return SubsidySearchResponse(
            schemes=schemes,
            total_matches=len(schemes),
            search_context={
                "sector": request.sector,
                "capex": request.capex,
                "state": request.state,
                "query": request.query
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search subsidies: {str(e)}"
        )


@router.get("/scheme/{scheme_id}")
async def get_subsidy_details(scheme_id: str):
    """
    Get detailed information about a specific subsidy scheme
    
    Returns complete scheme details, eligibility criteria,
    and application process
    """
    # TODO: Implement scheme details retrieval
    return {
        "success": True,
        "data": {
            "id": scheme_id,
            "message": "Scheme details retrieval not yet implemented"
        }
    }


@router.get("/categories")
async def get_subsidy_categories():
    """
    Get available subsidy categories and sectors
    
    Returns list of sectors and scheme types available
    """
    categories = {
        "sectors": [
            "Textile",
            "Manufacturing",
            "Food Processing",
            "Agriculture",
            "IT/Software",
            "Pharmaceuticals",
            "Services",
            "Women Entrepreneur",
            "Green Technology"
        ],
        "scheme_types": [
            "Capital Subsidy",
            "Interest Subvention",
            "Technology Upgrade",
            "Marketing Support",
            "Skill Development",
            "Infrastructure Support"
        ],
        "states": [
            "Gujarat",
            "Maharashtra",
            "Tamil Nadu",
            "Karnataka",
            "Telangana",
            "Andhra Pradesh",
            "Rajasthan",
            "Uttar Pradesh",
            "Punjab",
            "Haryana"
        ]
    }
    
    return {
        "success": True,
        "data": categories
    }


@router.get("/recent")
async def get_recent_subsidies(limit: int = 10):
    """
    Get recently added or updated subsidy schemes
    
    Returns schemes added in the last 30 days
    """
    # TODO: Implement recent subsidies query
    return {
        "success": True,
        "data": {
            "schemes": [],
            "total": 0,
            "limit": limit
        }
    }


@router.post("/refresh")
async def refresh_subsidy_database():
    """
    Manually refresh subsidy database
    
    Triggers Agent C to scrape government portals
    for latest schemes
    """
    try:
        from backend.agents.subsidy_hunter import refresh_schemes
        
        count = await refresh_schemes()
        
        return {
            "success": True,
            "message": f"Successfully refreshed {count} schemes",
            "data": {
                "schemes_updated": count
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh subsidy database: {str(e)}"
        )
