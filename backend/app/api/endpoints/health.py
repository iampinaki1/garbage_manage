"""
Health and System Diagnostics Endpoint.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.database.connection import db_manager
from backend.app.models.schemas import HealthResponse
from backend.app.services.pipeline_service import pipeline_service

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def get_health_status():
    """Reports operational health of backend services, ML models, and persistence store."""
    models_status = pipeline_service.get_model_health_status()
    db_status = db_manager.get_status()
    
    # Healthy if at least models and persistence layer are accessible
    is_healthy = models_status["model_a_classifier"]["weights_exist"] and models_status["model_b_detector"]["weights_exist"]
    
    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.VERSION,
        models=models_status,
        database=db_status
    )

