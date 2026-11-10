"""
Analytics and Environmental Aggregates Endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter
from backend.app.database.connection import db_manager
from backend.app.models.schemas import (
    AnalyticsResponse,
    CategoryBreakdown,
    RecyclabilityDistribution,
    AggregateImpact,
    EquivalentsMetrics
)
from backend.ml.preprocessing.class_mapping import CANONICAL_CATEGORIES, CANONICAL_TO_DISPLAY

router = APIRouter(tags=["Analytics"])

# Baseline reference benchmarks (EPA Municipal Solid Waste Characterization)
# used to initialize realistic analytics when fresh database has few records
BASELINE_CATEGORY_WEIGHTS = {
    "organic_waste": 0.28,
    "paper_waste": 0.23,
    "plastic_waste": 0.14,
    "metal_waste": 0.09,
    "glass_waste": 0.05,
    "textile_waste": 0.06,
    "electronic_waste": 0.03,
    "hazardous_waste": 0.02,
    "residual_waste": 0.10
}


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_system_analytics():
    """
    Returns aggregate waste segregation analytics, recyclability ratios,
    and cumulative environmental carbon & energy savings with EPA equivalencies.
    """
    analyses_col = db_manager.get_collection("analyses")
    records = await analyses_col.find({}).to_list()
    
    total_analyses = len(records)
    
    # Accumulate metrics
    cat_counts = {c: 0 for c in CANONICAL_CATEGORIES}
    cat_co2 = {c: 0.0 for c in CANONICAL_CATEGORIES}
    cat_energy = {c: 0.0 for c in CANONICAL_CATEGORIES}
    
    recyclable_count = 0
    non_recyclable_count = 0
    conditional_count = 0
    total_items = 0
    
    cumulative_co2 = 0.0
    cumulative_energy = 0.0
    
    for r in records:
        detections = r.get("detections", [])
        if not detections:
            # Fallback to summary
            summary = r.get("summary", {})
            cat = summary.get("primary_category", "residual_waste")
            if cat in cat_counts:
                cat_counts[cat] += 1
            total_items += 1
            co2 = summary.get("total_co2_saved_kg", 0.0)
            energy = summary.get("total_energy_saved_kwh", 0.0)
            cumulative_co2 += co2
            cumulative_energy += energy
            if summary.get("overall_recyclability") == "Recyclable":
                recyclable_count += 1
            else:
                non_recyclable_count += 1
            continue

        for det in detections:
            total_items += 1
            cat = det.get("category", "residual_waste")
            if cat in cat_counts:
                cat_counts[cat] += 1
            else:
                cat_counts["residual_waste"] += 1
                
            impact = det.get("environmental_impact", {})
            co2 = impact.get("estimated_co2_saved_kg", 0.0)
            energy = impact.get("estimated_energy_saved_kwh", 0.0)
            
            cat_co2[cat] = round(cat_co2.get(cat, 0.0) + co2, 4)
            cat_energy[cat] = round(cat_energy.get(cat, 0.0) + energy, 4)
            
            cumulative_co2 += co2
            cumulative_energy += energy
            
            if det.get("is_conditional"):
                conditional_count += 1
            elif det.get("is_recyclable"):
                recyclable_count += 1
            else:
                non_recyclable_count += 1

    display_total_items = max(total_items, 1)
    
    category_distribution: List[CategoryBreakdown] = []
    for cat in CANONICAL_CATEGORIES:
        count = cat_counts[cat]
        pct = round((count / display_total_items) * 100, 2) if total_items > 0 else 0.0
        category_distribution.append(
            CategoryBreakdown(
                category=cat,
                category_display=CANONICAL_TO_DISPLAY.get(cat, cat.replace("_", " ").title()),
                count=count,
                percentage=pct,
                co2_saved_kg=round(cat_co2[cat], 3),
                energy_saved_kwh=round(cat_energy[cat], 3)
            )
        )
        
    recyclable_pct = round((recyclable_count / display_total_items) * 100, 2) if total_items > 0 else 0.0

    # EPA Equivalencies:
    # 1 urban tree absorbs ~21.77 kg CO2 per year
    # 1 kWh charges ~80 smartphones (approx 12.5 Wh per charge)
    # Average passenger vehicle produces ~0.404 kg CO2 per mile (US EPA)
    tree_equiv = round(cumulative_co2 / 21.77, 2) if cumulative_co2 > 0 else 0.0
    phone_equiv = round(cumulative_energy * 80.0, 1) if cumulative_energy > 0 else 0.0
    miles_equiv = round(cumulative_co2 / 0.404, 2) if cumulative_co2 > 0 else 0.0

    return AnalyticsResponse(
        total_analyses=total_analyses,
        total_items=total_items,
        recyclability_distribution=RecyclabilityDistribution(
            recyclable_count=recyclable_count,
            non_recyclable_count=non_recyclable_count,
            conditional_count=conditional_count,
            recyclable_percentage=recyclable_pct
        ),
        category_distribution=category_distribution,
        aggregate_impact=AggregateImpact(
            total_analyses=total_analyses,
            total_waste_items=total_items,
            total_co2_saved_kg=round(cumulative_co2, 3),
            total_energy_saved_kwh=round(cumulative_energy, 3),
            equivalents=EquivalentsMetrics(
                trees_seedling_years_equivalent=tree_equiv,
                smartphone_charges_equivalent=phone_equiv,
                miles_driven_avoided=miles_equiv
            )
        )
    )

