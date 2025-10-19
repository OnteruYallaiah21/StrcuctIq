"""
API router configuration
"""

from fastapi import APIRouter
from app.api.v1.routes import router as receipts_router

api_router = APIRouter()

# Include all routers
api_router.include_router(receipts_router, tags=["receipts"])
