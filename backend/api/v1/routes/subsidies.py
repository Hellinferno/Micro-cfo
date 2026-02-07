"""
Subsidies API Routes
Subsidy Hunter - Agent C functionality
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from backend.agents.subsidy_hunter import SubsidyHunter


router = APIRouter()
hunter = SubsidyHunter()


# --- Schemas ---
class SubsidySearch(BaseModel):
    sector: str
    capex_amount: float
    state: Optional[str] = None
    turnover: Optional[float] = None


class Subsidy(BaseModel):
    name: str
    benefit: str
    eligibility: str
    ministry: str
    link: Optional[str] = None
    max_subsidy: Optional[str] = None
    match_score: Optional[float] = None


class SubsidyResponse(BaseModel):
    success: bool
    schemes: List[Subsidy] = []
    total: int = 0
    error: Optional[str] = None


# --- Routes ---
@router.post("/search", response_model=SubsidyResponse)
async def search_subsidies(search: SubsidySearch):
    """
    Find applicable government subsidies based on business profile
    """
    try:
        schemes = await hunter.find_subsidies(
            sector=search.sector,
            capex=search.capex_amount,
            state=search.state
        )
        return SubsidyResponse(success=True, schemes=schemes, total=len(schemes))
    except Exception as e:
        return SubsidyResponse(success=False, error=str(e))


@router.get("/sectors")
async def get_sectors():
    """Get list of supported business sectors"""
    return {
        "sectors": [
            "Manufacturing",
            "Textile",
            "Food Processing",
            "Agriculture",
            "IT/Technology",
            "Pharma",
            "Services",
            "Women Entrepreneur",
            "Rural Business"
        ]
    }


@router.get("/states")
async def get_states():
    """Get list of Indian states with subsidy programs"""
    return {
        "states": [
            "All India",
            "Maharashtra",
            "Gujarat",
            "Karnataka",
            "Tamil Nadu",
            "Uttar Pradesh",
            "Rajasthan",
            "Madhya Pradesh",
            "West Bengal",
            "Telangana",
            "Andhra Pradesh",
            "Kerala"
        ]
    }


@router.get("/applications")
async def get_applications():
    """Get user's subsidy applications"""
    # TODO: Implement with database
    return {"applications": [], "total": 0}
