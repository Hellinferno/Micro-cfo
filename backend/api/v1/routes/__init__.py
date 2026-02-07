"""
API v1 Router
Aggregates all v1 route modules
"""

from fastapi import APIRouter
from backend.api.v1.routes.health import router as health_router
from backend.api.v1.routes.invoices import router as invoices_router
from backend.api.v1.routes.compliance import router as compliance_router
from backend.api.v1.routes.subsidies import router as subsidies_router
from backend.api.v1.routes.negotiation import router as negotiation_router
from backend.api.v1.routes.chat import router as chat_router

router = APIRouter()

# Include all route modules
router.include_router(health_router, tags=["Health"])
router.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
router.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])
router.include_router(subsidies_router, prefix="/subsidies", tags=["Subsidies"])
router.include_router(negotiation_router, prefix="/negotiation", tags=["Negotiation"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
