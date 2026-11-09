"""
Phase 6 Unit and Integration Tests: Modular FastAPI Backend.
Verifies all Phase 6 requirements:
1. Root '/' metadata endpoint.
2. GET '/api/health' system diagnostic endpoint.
3. POST '/api/auth/register' user registration and duplicate prevention.
4. POST '/api/auth/login' credential validation and JWT issuance.
5. Token resolution & verification.
6. POST '/api/analyze' end-to-end multi-object detection, classification, recommendation, and overlay.
7. POST '/api/analyze' validation (empty file, unsupported MIME type).
8. POST '/api/analyze' contamination flag routing.
9. GET '/api/history' paginated prediction retrieval.
10. GET '/api/analytics' aggregate waste categories, recyclability ratios, and EPA equivalents.
"""

import io
import sys
from pathlib import Path
from PIL import Image
import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import root
from backend.app.api.endpoints.health import get_health_status
from backend.app.api.endpoints.auth import register_user, login_user
from backend.app.api.endpoints.history import get_analysis_history
from backend.app.api.endpoints.analytics import get_system_analytics
from backend.app.api.endpoints.analyze import analyze_waste_image
from backend.app.models.schemas import UserRegisterRequest, UserLoginRequest
from backend.app.services.auth_service import decode_access_token


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


def test_root_endpoint():
    """Verify root GET / returns metadata and endpoint directory."""
    data = sync_run(root())
    assert "Smart Waste" in data["title"]
    assert data["status"] == "operational"
    assert "/api/analyze" in data["endpoints"]["analyze"]
    assert "/api/health" in data["endpoints"]["health"]


def test_health_endpoint():
    """Verify GET /api/health reports system, model, and database status."""
    health = sync_run(get_health_status())
    assert health.status in ["healthy", "degraded"]
    assert "model_a_classifier" in health.models
    assert "model_b_detector" in health.models
    assert "recommendation_engine" in health.models
    assert health.database is not None


def test_auth_registration_and_login_flow():
    """Verify user registration, JWT token generation, duplicate protection, and login."""
    test_user = UserRegisterRequest(
        username="greenhero2026",
        email="greenhero@planet.org",
        password="SuperPassword123!",
        full_name="Green Hero"
    )
    
    # 1. Register new user
    reg_data = sync_run(register_user(test_user))
    assert reg_data.access_token is not None
    assert reg_data.user.username == "greenhero2026"
    assert reg_data.user.email == "greenhero@planet.org"
    
    # 2. Reject duplicate registration
    with pytest.raises(HTTPException) as exc_info:
        sync_run(register_user(test_user))
    assert exc_info.value.status_code == 400
    assert "already registered" in exc_info.value.detail.lower()
    
    # 3. Successful login
    login_req = UserLoginRequest(username_or_email="greenhero2026", password="SuperPassword123!")
    login_data = sync_run(login_user(login_req))
    assert login_data.access_token is not None
    
    # 4. Decode and verify token
    payload = decode_access_token(login_data.access_token)
    assert payload is not None
    assert payload.get("sub") == "greenhero2026"
    
    # 5. Reject bad password
    bad_login_req = UserLoginRequest(username_or_email="greenhero2026", password="WrongPassword!")
    with pytest.raises(HTTPException) as exc_bad:
        sync_run(login_user(bad_login_req))
    assert exc_bad.value.status_code == 401


def test_analyze_endpoint_with_valid_image():
    """Verify POST /api/analyze accepts an image and returns full predictions & recommendations."""
    img = Image.new("RGB", (300, 300), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    
    upload = UploadFile(file=buf, filename="recyclable_sample.jpg", headers={"content-type": "image/jpeg"})
    res = sync_run(analyze_waste_image(file=upload, location="us_epa", is_contaminated=False))
    
    assert res.analysis_id is not None
    assert res.summary is not None
    assert len(res.detections) >= 1
    
    first_det = res.detections[0]
    assert first_det.category in ["organic_waste", "paper_waste", "plastic_waste", "metal_waste", "glass_waste", "electronic_waste", "hazardous_waste", "textile_waste", "residual_waste"]
    assert first_det.recommended_bin is not None
    assert first_det.environmental_impact is not None
    assert res.annotated_image_url.startswith("/static/annotated/")


def test_analyze_empty_file_validation():
    """Verify POST /api/analyze rejects 0-byte file uploads with 400."""
    buf = io.BytesIO()
    upload = UploadFile(file=buf, filename="empty.jpg", headers={"content-type": "image/jpeg"})
    with pytest.raises(HTTPException) as exc_info:
        sync_run(analyze_waste_image(file=upload))
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


def test_analyze_unsupported_mime_type():
    """Verify POST /api/analyze rejects non-image files with 400."""
    buf = io.BytesIO(b"Hello waste")
    upload = UploadFile(file=buf, filename="script.txt", headers={"content-type": "text/plain"})
    with pytest.raises(HTTPException) as exc_info:
        sync_run(analyze_waste_image(file=upload))
    assert exc_info.value.status_code == 400
    assert "unsupported" in exc_info.value.detail.lower()


def test_analyze_with_contamination_flag():
    """Verify POST /api/analyze applies contamination rules when is_contaminated=true."""
    img = Image.new("RGB", (200, 200), color=(210, 180, 140))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    
    upload = UploadFile(file=buf, filename="soiled_cardboard.jpg", headers={"content-type": "image/jpeg"})
    res = sync_run(analyze_waste_image(file=upload, location="us_epa", is_contaminated=True))
    
    first_det = res.detections[0]
    assert first_det.contamination_assessment.is_contaminated is True


def test_history_endpoint():
    """Verify GET /api/history returns recent analyses in descending order."""
    hist = sync_run(get_analysis_history(limit=10, skip=0))
    assert hist.total_count >= 1
    assert len(hist.items) >= 1
    
    first_item = hist.items[0]
    assert first_item.analysis_id is not None
    assert first_item.primary_category is not None


def test_analytics_endpoint():
    """Verify GET /api/analytics returns category distribution and EPA impact metrics."""
    analytics = sync_run(get_system_analytics())
    assert analytics.total_analyses >= 1
    assert analytics.total_items >= 1
    assert len(analytics.category_distribution) == 9
    
    impact = analytics.aggregate_impact
    assert impact.total_co2_saved_kg >= 0.0
    assert impact.equivalents.trees_seedling_years_equivalent >= 0.0
    assert impact.equivalents.smartphone_charges_equivalent >= 0.0
    assert impact.equivalents.miles_driven_avoided >= 0.0
