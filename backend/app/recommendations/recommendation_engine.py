"""
FastAPI application proxy for Recycling Recommendation Engine.
Imports from backend.recommendations.recommendation_engine.
"""

from backend.recommendations.recommendation_engine import (
    RecyclingRecommendationEngine,
    get_recommendation_engine,
    LOCATION_PROFILES,
    AVERAGE_ITEM_WEIGHTS_KG,
    DEFAULT_CSV_PATHS
)

__all__ = [
    "RecyclingRecommendationEngine",
    "get_recommendation_engine",
    "LOCATION_PROFILES",
    "AVERAGE_ITEM_WEIGHTS_KG",
    "DEFAULT_CSV_PATHS"
]

