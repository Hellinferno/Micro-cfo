"""
Compliance API Routes
Legal Sentinel - Agent B functionality
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from backend.agents.legal_sentinel import LegalSentinel


router = APIRouter()
sentinel = LegalSentinel()


# --- Schemas ---
class ComplianceQuery(BaseModel):
    query: str
    user_context: Optional[str] = None


class ComplianceResult(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH
    relevant_section: str
    explanation: str
    compliant_action: str


class ComplianceResponse(BaseModel):
    success: bool
    data: Optional[ComplianceResult] = None
    error: Optional[str] = None


# --- Routes ---
@router.post("/query", response_model=ComplianceResponse)
async def check_compliance(query: ComplianceQuery):
    """
    Ask a compliance question and get risk assessment
    """
    try:
        result = await sentinel.analyze(query.query, query.user_context)
        return ComplianceResponse(success=True, data=result)
    except Exception as e:
        return ComplianceResponse(success=False, error=str(e))


@router.get("/history")
async def get_compliance_history():
    """Get user's compliance query history"""
    # TODO: Implement with database
    return {"queries": [], "total": 0}


@router.get("/quick-answers")
async def get_quick_answers():
    """Common compliance questions with pre-computed answers"""
    return {
        "questions": [
            {
                "question": "Can I claim ITC on food and beverages?",
                "answer": "Generally NO. Section 17(5) of CGST Act blocks ITC on food & beverages except when used for further supply or as part of taxable services.",
                "risk_level": "MEDIUM"
            },
            {
                "question": "What is the GST rate for software services?",
                "answer": "18% GST for software development and IT services under SAC 998314.",
                "risk_level": "LOW"
            },
            {
                "question": "When is GSTR-3B due?",
                "answer": "20th of the following month for regular taxpayers. QRMP scheme allows quarterly filing.",
                "risk_level": "HIGH" 
            }
        ]
    }
