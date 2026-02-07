"""Health check routes"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def api_health():
    return {"status": "ok", "api": "v1"}
