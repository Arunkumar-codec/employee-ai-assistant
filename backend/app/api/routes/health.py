"""
Health check endpoint.

WHAT: Simple liveness endpoint.
WHY:  Assessment/Day-1 plan requires a working, verifiable API before any
      AI logic is built, and it gives the frontend something real to call.
"""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.app_name}
