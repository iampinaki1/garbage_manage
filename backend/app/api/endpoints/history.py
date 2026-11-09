"""
Analysis History Retrieval Endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Query
from backend.app.database.connection import db_manager
from backend.app.models.schemas import HistoryResponse, HistoryItem

router = APIRouter(tags=["History"])


@router.get("/history", response_model=HistoryResponse)
async def get_analysis_history(
    limit: int = Query(50, ge=1, le=100, description="Max number of past records to return"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    category: Optional[str] = Query(None, description="Filter by canonical waste category")
):
    """
    Fetches paginated previous waste predictions and visual overlays.
    """
    analyses_col = db_manager.get_collection("analyses")
    
    limit_val = limit if isinstance(limit, int) else 50
    skip_val = skip if isinstance(skip, int) else 0
    
    query = {}
    if category and isinstance(category, str):
        query["summary.primary_category"] = category.strip().lower()
        
    cursor = analyses_col.find(query).sort("timestamp", -1).skip(skip_val).limit(limit_val)
    records = await cursor.to_list(length=limit_val)
    total_count = await analyses_col.count_documents(query)
    
    items: List[HistoryItem] = []
    for r in records:
        summary = r.get("summary", {})
        impact = r.get("total_environmental_impact", {})
        
        items.append(
            HistoryItem(
                analysis_id=r.get("analysis_id", str(r.get("_id", ""))),
                timestamp=r.get("timestamp", ""),
                primary_category=summary.get("primary_category", "unclassified"),
                primary_category_display=summary.get("primary_category_display", "Unclassified"),
                total_objects=summary.get("total_objects_detected", 1),
                overall_recyclability=summary.get("overall_recyclability", "Unknown"),
                total_co2_saved_kg=summary.get("total_co2_saved_kg", impact.get("estimated_co2_saved_kg", 0.0)),
                total_energy_saved_kwh=summary.get("total_energy_saved_kwh", impact.get("estimated_energy_saved_kwh", 0.0)),
                annotated_image_url=r.get("annotated_image_url")
            )
        )
        
    return HistoryResponse(
        total_count=total_count,
        items=items
    )
