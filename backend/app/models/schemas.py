"""
Pydantic v2 schemas for API requests, responses, and database models.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ==========================================
# Auth Schemas
# ==========================================
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserProfile


# ==========================================
# Waste Detection & Segregation Schemas
# ==========================================
class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    width: int
    height: int


class ContaminationInfo(BaseModel):
    risk_level: str
    is_contaminated: bool
    contamination_notes: str
    action_taken: str


class EnvironmentalImpactInfo(BaseModel):
    estimated_co2_saved_kg: float
    estimated_energy_saved_kwh: float
    assumed_weight_kg: float
    factors_used: Optional[Dict[str, float]] = None
    disclaimer: str
    reference_source: str


class DetectedObject(BaseModel):
    object_id: int
    category: str
    category_display: str
    matched_item: str
    material: str
    confidence: float
    is_recyclable: bool
    is_conditional: bool
    recyclability_status: str
    recommended_bin: str
    recycling_method: str
    preparation_instructions: str
    disposal_instructions: str
    box_pixels: Optional[BoundingBox] = None
    box_normalized: Optional[List[float]] = None
    contamination_assessment: ContaminationInfo
    environmental_impact: EnvironmentalImpactInfo


class AnalysisSummary(BaseModel):
    total_objects_detected: int
    primary_category: str
    primary_category_display: str
    overall_recyclability: str
    total_co2_saved_kg: float
    total_energy_saved_kwh: float
    inference_latency_ms: float


class AnalyzeResponse(BaseModel):
    analysis_id: str
    timestamp: str
    location_profile: str
    image_url: Optional[str] = None
    annotated_image_url: Optional[str] = None
    summary: AnalysisSummary
    detections: List[DetectedObject]
    total_environmental_impact: EnvironmentalImpactInfo


# ==========================================
# History Schemas
# ==========================================
class HistoryItem(BaseModel):
    analysis_id: str
    timestamp: str
    primary_category: str
    primary_category_display: str
    total_objects: int
    overall_recyclability: str
    total_co2_saved_kg: float
    total_energy_saved_kwh: float
    annotated_image_url: Optional[str] = None


class HistoryResponse(BaseModel):
    total_count: int
    items: List[HistoryItem]


# ==========================================
# Analytics Schemas
# ==========================================
class CategoryBreakdown(BaseModel):
    category: str
    category_display: str
    count: int
    percentage: float
    co2_saved_kg: float
    energy_saved_kwh: float


class RecyclabilityDistribution(BaseModel):
    recyclable_count: int
    non_recyclable_count: int
    conditional_count: int
    recyclable_percentage: float


class EquivalentsMetrics(BaseModel):
    trees_seedling_years_equivalent: float
    smartphone_charges_equivalent: float
    miles_driven_avoided: float


class AggregateImpact(BaseModel):
    total_analyses: int
    total_waste_items: int
    total_co2_saved_kg: float
    total_energy_saved_kwh: float
    equivalents: EquivalentsMetrics


class AnalyticsResponse(BaseModel):
    total_analyses: int
    total_items: int
    recyclability_distribution: RecyclabilityDistribution
    category_distribution: List[CategoryBreakdown]
    aggregate_impact: AggregateImpact


# ==========================================
# Health Schemas
# ==========================================
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    models: Dict[str, Any]
    database: Dict[str, Any]
