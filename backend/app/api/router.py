"""
Central API router combining all subsystem routers.
"""

from fastapi import APIRouter
from backend.app.api.endpoints import health, auth, analyze, history, analytics

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(analyze.router)
api_router.include_router(history.router)
api_router.include_router(analytics.router)

