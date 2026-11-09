"""
Phase 5 Unit Tests: Recycling Recommendation Engine & Environmental Impact Calculations.
Tests:
- CSV schema validity and documentation citations
- Complete coverage across all 9 canonical waste categories
- Localized bin routing (US EPA, EU Standard, UK WRAP, India CPCB)
- Contamination sensitivity and automatic recyclability demotion
- Documented environmental impact calculations (CO2 and Energy)
- Conditional and non-recyclable material classifications
- Robust fallback for unknown categories
"""

import pytest
from pathlib import Path
import csv

from backend.recommendations.recommendation_engine import (
    RecyclingRecommendationEngine,
    get_recommendation_engine,
    LOCATION_PROFILES,
    AVERAGE_ITEM_WEIGHTS_KG,
    DEFAULT_CSV_PATHS
)
from backend.ml.preprocessing.class_mapping import CANONICAL_CATEGORIES

ROOT = Path(__file__).resolve().parent.parent.parent


def test_csv_file_existence_and_schema():
    """Verify recycling_data.csv exists in both target locations and adheres to expected schema."""
    csv_path = ROOT / "backend" / "recommendations" / "recycling_data.csv"
    assert csv_path.exists(), f"Primary CSV missing at {csv_path}"
    
    app_csv_path = ROOT / "backend" / "app" / "recommendations" / "recycling_data.csv"
    assert app_csv_path.exists(), f"App copy missing at {app_csv_path}"
    
    expected_headers = [
        "object_name", "material", "waste_category", "recyclable",
        "recommended_bin", "recycling_method", "preparation_instructions",
        "disposal_instructions", "contamination_risk", "contamination_notes",
        "co2_saved_kg_per_kg", "energy_saved_kwh_per_kg", "reference_source"
    ]
    
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == expected_headers, f"Header mismatch: {reader.fieldnames}"
        rows = list(reader)
        assert len(rows) >= 30, f"Expected at least 30 entries, got {len(rows)}"
        
        for idx, row in enumerate(rows):
            assert row["object_name"], f"Row {idx} missing object_name"
            assert row["waste_category"] in CANONICAL_CATEGORIES, f"Row {idx} invalid category: {row['waste_category']}"
            assert row["recyclable"] in ["true", "false", "conditional"], f"Row {idx} invalid recyclable: {row['recyclable']}"
            assert float(row["co2_saved_kg_per_kg"]) >= 0.0, f"Row {idx} negative CO2 factor"
            assert float(row["energy_saved_kwh_per_kg"]) >= 0.0, f"Row {idx} negative Energy factor"
            assert row["reference_source"], f"Row {idx} missing citation"


def test_all_canonical_categories_indexed():
    """Verify every single canonical waste category is represented in the recommendation database."""
    engine = get_recommendation_engine()
    for cat in CANONICAL_CATEGORIES:
        assert cat in engine.category_index, f"Canonical category '{cat}' missing from recommendation index"
        assert len(engine.category_index[cat]) > 0, f"No items listed for category '{cat}'"


def test_engine_recommendation_structure():
    """Verify structured output fields required for FastAPI and Frontend consumption."""
    engine = get_recommendation_engine()
    rec = engine.get_recommendation(
        category="plastic_waste",
        query_item="PET Water Bottle",
        location="us_epa"
    )
    
    required_keys = [
        "category", "category_display", "matched_item", "material",
        "is_recyclable", "is_conditional", "recyclability_status",
        "recommended_bin", "recycling_method", "preparation_instructions",
        "disposal_instructions", "contamination_assessment",
        "environmental_impact", "location_context"
    ]
    for k in required_keys:
        assert k in rec, f"Missing required top-level key: {k}"
        
    assert rec["category"] == "plastic_waste"
    assert rec["is_recyclable"] is True
    assert "Blue Bin" in rec["recommended_bin"]
    assert rec["environmental_impact"]["estimated_co2_saved_kg"] > 0
    assert rec["environmental_impact"]["estimated_energy_saved_kwh"] > 0
    assert "EPA WARM" in rec["environmental_impact"]["disclaimer"]


def test_location_specific_bin_routing():
    """Verify location-specific disposal rules (US EPA vs EU Standard vs India CPCB)."""
    engine = get_recommendation_engine()
    
    # 1. Aluminium can in EU standard -> Yellow Bin (Gelber Sack)
    rec_eu = engine.get_recommendation(category="metal_waste", query_item="Aluminium Beverage Can", location="eu_standard")
    assert "Yellow Bin" in rec_eu["recommended_bin"] or "Gelber Sack" in rec_eu["recommended_bin"]
    
    # 2. Aluminium can in US EPA -> Blue Bin
    rec_us = engine.get_recommendation(category="metal_waste", query_item="Aluminium Beverage Can", location="us_epa")
    assert "Blue Bin" in rec_us["recommended_bin"]
    
    # 3. Organic waste in India CPCB -> Green Bin (Wet Waste)
    rec_in = engine.get_recommendation(category="organic_waste", query_item="Banana Peel", location="india_cpcb")
    assert "Green Bin" in rec_in["recommended_bin"]
    assert "Wet Waste" in rec_in["recommended_bin"]
    
    # 4. Battery in India CPCB -> Authorized E-Waste & Hazardous Collection
    rec_bat = engine.get_recommendation(category="hazardous_waste", query_item="Alkaline / Lithium Battery", location="india_cpcb")
    assert "Authorized" in rec_bat["recommended_bin"] or "Hazardous" in rec_bat["recommended_bin"]


def test_contamination_override_logic():
    """Verify contamination changes clean paper from recyclable to non-recyclable."""
    engine = get_recommendation_engine()
    
    # Clean cardboard box -> Recyclable
    clean_box = engine.get_recommendation(category="paper_waste", query_item="Cardboard Box", is_contaminated=False)
    assert clean_box["is_recyclable"] is True
    assert clean_box["environmental_impact"]["estimated_co2_saved_kg"] > 0
    
    # Contaminated cardboard / greasy paper -> Non-Recyclable, 0 environmental savings
    soiled_box = engine.get_recommendation(category="paper_waste", query_item="Cardboard Box", is_contaminated=True)
    assert soiled_box["is_recyclable"] is False
    assert soiled_box["contamination_assessment"]["is_contaminated"] is True
    assert "CONTAMINATION ALERT" in soiled_box["contamination_assessment"]["action_taken"]
    assert soiled_box["environmental_impact"]["estimated_co2_saved_kg"] == 0.0
    assert soiled_box["environmental_impact"]["estimated_energy_saved_kwh"] == 0.0


def test_non_recyclable_items_detection():
    """Verify that inherently non-recyclable items are correctly rejected."""
    engine = get_recommendation_engine()
    
    # Styrofoam
    rec_styro = engine.get_recommendation(category="plastic_waste", query_item="Polystyrene Foam / Styrofoam")
    assert rec_styro["is_recyclable"] is False
    assert "Non-Recyclable" in rec_styro["recyclability_status"]
    
    # Diaper
    rec_diaper = engine.get_recommendation(category="residual_waste", query_item="Disposable Baby Diaper")
    assert rec_diaper["is_recyclable"] is False
    assert "Black" in rec_diaper["recommended_bin"] or "Landfill" in rec_diaper["recommended_bin"]
    
    # Ceramic mug
    rec_ceramic = engine.get_recommendation(category="glass_waste", query_item="Ceramic Plate / Mug")
    assert rec_ceramic["is_recyclable"] is False


def test_conditional_recyclability():
    """Verify conditional materials like plastic film/bags are routed away from curbside bins."""
    engine = get_recommendation_engine()
    rec_bag = engine.get_recommendation(category="plastic_waste", query_item="Plastic Grocery Bag / Film", location="us_epa")
    assert rec_bag["is_conditional"] is True
    assert "Conditionally Recyclable" in rec_bag["recyclability_status"]
    assert "Supermarket" in rec_bag["recommended_bin"] or "Store Drop-off" in rec_bag["recommended_bin"]


def test_custom_weight_impact_scaling():
    """Verify environmental metrics scale linearly with custom weight input."""
    engine = get_recommendation_engine()
    # 1.0 kg of Aluminium
    rec_1kg = engine.get_recommendation(category="metal_waste", query_item="Aluminium Beverage Can", custom_weight_kg=1.0)
    assert rec_1kg["environmental_impact"]["assumed_weight_kg"] == 1.0
    assert rec_1kg["environmental_impact"]["estimated_co2_saved_kg"] == 9.1
    assert rec_1kg["environmental_impact"]["estimated_energy_saved_kwh"] == 14.0
    
    # 2.0 kg of Aluminium (doubled)
    rec_2kg = engine.get_recommendation(category="metal_waste", query_item="Aluminium Beverage Can", custom_weight_kg=2.0)
    assert rec_2kg["environmental_impact"]["estimated_co2_saved_kg"] == 18.2
    assert rec_2kg["environmental_impact"]["estimated_energy_saved_kwh"] == 28.0


def test_unknown_category_graceful_fallback():
    """Verify unknown category input does not raise exceptions and yields safe default guidance."""
    engine = get_recommendation_engine()
    rec_unknown = engine.get_recommendation(category="radioactive_waste_unspecified")
    assert rec_unknown["is_recyclable"] is False
    assert "Black" in rec_unknown["recommended_bin"] or "Landfill" in rec_unknown["recommended_bin"]
    assert rec_unknown["environmental_impact"]["estimated_co2_saved_kg"] == 0.0
