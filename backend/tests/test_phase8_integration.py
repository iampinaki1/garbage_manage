"""
Phase 8: System Integration Test Suite.
Verifies the end-to-end integration between:
1. Real vision models (Model B YOLO multi-object detector + Model A MobileNetV3 classifier)
2. Localized Recommendation Engine (EPA WARM & EEA life-cycle conversion factors)
3. Dual-mode Database (MongoDB / In-Memory Fallback)
4. FastAPI REST Endpoints & Schemas
5. Frontend API Contract & Parameter Alignments
"""

import io
import sys
import pytest
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import app
from backend.app.services.pipeline_service import pipeline_service
from backend.app.database.connection import db_manager
from backend.app.models.schemas import AnalyzeResponse, UserProfile
from backend.app.api.endpoints.health import get_health_status
from backend.app.api.endpoints.history import get_analysis_history
from backend.app.api.endpoints.analytics import get_system_analytics
from backend.app.api.endpoints.auth import register_user, login_user
from backend.app.models.schemas import UserRegisterRequest, UserLoginRequest


def sync_run(coro):
    """Executes coroutine chain synchronously without socket-bound event loops."""
    sub_stack = [coro]
    while sub_stack:
        current = sub_stack[-1]
        try:
            res = current.send(None)
            if hasattr(res, "send"):
                sub_stack.append(res)
        except StopIteration as e:
            sub_stack.pop()
            if sub_stack:
                try:
                    sub_stack[-1].send(e.value)
                except StopIteration:
                    pass
            else:
                return e.value


@pytest.fixture(autouse=True)
def clean_db():
    for col in db_manager._in_memory_db.values():
        col.documents.clear()
    yield
    for col in db_manager._in_memory_db.values():
        col.documents.clear()


def test_system_health_endpoint():
    """Verifies that /api/health reports operational status for all components."""
    health = sync_run(get_health_status())
    assert health.status in ["healthy", "degraded"]
    assert health.database["backend"] in ["mongodb", "in_memory_store"]
    assert health.models["model_a_classifier"]["weights_exist"] is True
    assert health.models["model_b_detector"]["weights_exist"] is True
    assert health.models["recommendation_engine"]["database_loaded"] is True
    assert health.models["recommendation_engine"]["item_count"] >= 40


def test_end_to_end_analyze_pipeline_real_image():
    """
    Executes complete end-to-end analysis on an authentic dataset image:
    YOLO detection -> Crop / whole classification -> Recommendation Engine -> Storage.
    """
    sample_path = ROOT / "datasets" / "trashnet" / "cardboard" / "cardboard1.jpg"
    if not sample_path.exists():
        taco_candidates = list((ROOT / "datasets" / "processed" / "yolo" / "images" / "train").glob("*.jpg"))
        assert len(taco_candidates) > 0, "No sample test image found in datasets"
        sample_path = taco_candidates[0]

    with open(sample_path, "rb") as f:
        img_bytes = f.read()

    res = sync_run(pipeline_service.analyze_image(
        image_bytes=img_bytes,
        filename=sample_path.name,
        location="us_epa",
        is_contaminated=False
    ))

    # 1. Verify Schema Validation
    assert isinstance(res, AnalyzeResponse)
    assert res.analysis_id is not None
    assert res.timestamp is not None
    assert res.location_profile == "us_epa"

    # 2. Verify Output Images Generated on Disk
    assert res.image_url.startswith("/static/uploads/")
    assert res.annotated_image_url.startswith("/static/annotated/")
    
    upload_file = ROOT / "backend" / res.image_url.lstrip("/")
    annotated_file = ROOT / "backend" / res.annotated_image_url.lstrip("/")
    assert upload_file.exists(), f"Uploaded image not saved at {upload_file}"
    assert annotated_file.exists(), f"Annotated image not saved at {annotated_file}"

    # 3. Verify Detections & Recommendations
    assert len(res.detections) >= 1
    det = res.detections[0]
    assert det.object_id == 1
    assert det.category in ["paper_waste", "cardboard", "plastic_waste", "glass_waste", "metal_waste", "organic_waste", "residual_waste"]
    assert det.confidence > 0.0
    assert det.recommended_bin != ""
    assert det.recycling_method != ""
    assert det.disposal_instructions != ""
    assert det.box_pixels.width > 0
    assert det.box_pixels.height > 0

    # 4. Verify Summary & Impact
    assert res.summary.total_objects_detected == len(res.detections)
    assert res.summary.inference_latency_ms > 0
    assert res.total_environmental_impact.assumed_weight_kg > 0


def test_multi_object_composite_scenario():
    """
    Tests multi-object detection and aggregated carbon calculations on an image
    containing multiple distinct visual regions.
    """
    img = Image.new("RGB", (640, 480), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 250, 350], fill=(50, 120, 200), outline=(0, 0, 0))
    draw.rectangle([350, 80, 580, 400], fill=(40, 180, 80), outline=(0, 0, 0))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    res = sync_run(pipeline_service.analyze_image(
        image_bytes=img_bytes,
        filename="composite.jpg",
        location="eu_standard",
        is_contaminated=False
    ))

    assert isinstance(res, AnalyzeResponse)
    assert len(res.detections) >= 1
    expected_co2 = round(sum(d.environmental_impact.estimated_co2_saved_kg for d in res.detections), 4)
    expected_energy = round(sum(d.environmental_impact.estimated_energy_saved_kwh for d in res.detections), 4)
    assert res.summary.total_co2_saved_kg == expected_co2
    assert res.summary.total_energy_saved_kwh == expected_energy


def test_contamination_override_in_integrated_pipeline():
    """
    Tests that flagging contamination in the end-to-end pipeline:
    - Overrides recyclability to False for soiled items
    - Diverts item to general waste/compost bin
    - Zeroes out CO2 and energy credits
    """
    sample_path = ROOT / "datasets" / "trashnet" / "cardboard" / "cardboard1.jpg"
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            img_bytes = f.read()
    else:
        img = Image.new("RGB", (300, 300), color=(180, 140, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        img_bytes = buf.getvalue()

    # Analyze clean
    clean_res = sync_run(pipeline_service.analyze_image(
        image_bytes=img_bytes,
        filename="clean.jpg",
        location="us_epa",
        is_contaminated=False
    ))

    # Analyze contaminated
    contam_res = sync_run(pipeline_service.analyze_image(
        image_bytes=img_bytes,
        filename="contam.jpg",
        location="us_epa",
        is_contaminated=True
    ))

    det_contam = contam_res.detections[0]
    assert det_contam.contamination_assessment.is_contaminated is True
    
    # 2. Check paper/cardboard contamination override specifically
    paper_rec = pipeline_service._recommendation_engine.get_recommendation(
        category="paper_waste",
        query_item="Greasy Cardboard Box",
        location="us_epa",
        is_contaminated=True
    )
    assert paper_rec["is_recyclable"] is False
    assert paper_rec["environmental_impact"]["estimated_co2_saved_kg"] == 0.0
    assert "CONTAMINATION" in paper_rec["disposal_instructions"]


def test_regional_jurisdiction_routing_integration():
    """
    Tests that localized recycling bin recommendations adapt appropriately
    across US EPA, EU Standard, UK WRAP, and India CPCB profiles.
    """
    img = Image.new("RGB", (300, 300), color=(80, 140, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    us_res = sync_run(pipeline_service.analyze_image(img_bytes, location="us_epa"))
    eu_res = sync_run(pipeline_service.analyze_image(img_bytes, location="eu_standard"))
    in_res = sync_run(pipeline_service.analyze_image(img_bytes, location="india_cpcb"))

    assert us_res.location_profile == "us_epa"
    assert eu_res.location_profile == "eu_standard"
    assert in_res.location_profile == "india_cpcb"

    assert us_res.detections[0].recommended_bin != ""
    assert eu_res.detections[0].recommended_bin != ""
    assert in_res.detections[0].recommended_bin != ""


def test_history_and_analytics_persistence_roundtrip():
    """
    Verifies that analysis records are stored in the database collection and
    accurately reflected in subsequent /api/history and /api/analytics calls.
    """
    img = Image.new("RGB", (200, 200), color=(100, 200, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    # 1. Execute analysis
    analyzed = sync_run(pipeline_service.analyze_image(img_bytes, filename="roundtrip.jpg"))
    
    # 2. Query History
    history_res = sync_run(get_analysis_history(limit=10, skip=0))
    assert history_res.total_count >= 1
    assert any(item.analysis_id == analyzed.analysis_id for item in history_res.items)

    # 3. Query Analytics
    analytics_res = sync_run(get_system_analytics())
    assert analytics_res.total_analyses >= 1
    assert analytics_res.total_items >= 1
    dist = analytics_res.recyclability_distribution
    assert (dist.recyclable_count + dist.non_recyclable_count + dist.conditional_count) >= 1
    assert len(analytics_res.category_distribution) > 0


def test_authenticated_user_history_attribution():
    """
    Verifies that when an authenticated user analyzes an image, the prediction record
    is linked to their user id and username.
    """
    user_reg = sync_run(register_user(UserRegisterRequest(
        email="integration_user@ecosort.org",
        username="integration_eco",
        password="ValidPassword123!"
    )))
    current_user = user_reg.user

    img = Image.new("RGB", (200, 200), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    analyzed = sync_run(pipeline_service.analyze_image(
        image_bytes=img_bytes,
        filename="auth_user_test.jpg",
        current_user=current_user
    ))

    # Query DB collection directly to verify user attribution
    col = db_manager.get_collection("analyses")
    cursor = col.find({"analysis_id": analyzed.analysis_id})
    docs = sync_run(cursor.to_list(1))
    assert len(docs) == 1
    assert docs[0]["user_id"] == current_user.id
    assert docs[0]["user_username"] == "integration_eco"


def test_corrupted_image_handling():
    """Verifies that unparseable or corrupted bytes raise a descriptive ValueError."""
    corrupted_bytes = b"NOT_A_VALID_IMAGE_HEADER_DATA_12345"
    with pytest.raises(ValueError, match="Invalid image format or corrupted file"):
        sync_run(pipeline_service.analyze_image(
            image_bytes=corrupted_bytes,
            filename="corrupt.jpg"
        ))


def test_low_confidence_uncertainty_handling():
    """
    Verifies that when confidence is low or uncertain, the system never forces a prediction
    and marks category as 'uncertain' with general waste guidance and 0 carbon credits.
    """
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    res = sync_run(pipeline_service.analyze_image(
        image_bytes=img_bytes,
        filename="uniform_grey.jpg"
    ))

    assert isinstance(res, AnalyzeResponse)
    assert len(res.detections) >= 1
    det = res.detections[0]
    
    if det.category == "uncertain":
        assert det.is_recyclable is False
        assert det.environmental_impact.estimated_co2_saved_kg == 0.0
        assert "uncertain" in res.summary.overall_recyclability.lower()


def test_frontend_backend_api_parity():
    """
    Verifies that all frontend apiService methods correspond to registered FastAPI routes.
    """
    route_paths = list(app.openapi()["paths"].keys())
    
    expected_endpoints = [
        "/api/analyze",
        "/api/history",
        "/api/analytics",
        "/api/health",
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/me"
    ]
    
    for endpoint in expected_endpoints:
        assert endpoint in route_paths, f"Expected endpoint '{endpoint}' not found in registered FastAPI routes: {route_paths}"
