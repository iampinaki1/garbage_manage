"""
Waste Analysis and Classification Endpoint.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from backend.app.core.config import settings
from backend.app.models.schemas import AnalyzeResponse, UserProfile
from backend.app.services.auth_service import get_optional_current_user
from backend.app.services.pipeline_service import pipeline_service

router = APIRouter(tags=["Waste Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_waste_image(
    file: UploadFile = File(..., description="Waste image file (JPEG, PNG, WebP)"),
    location: str = Form("us_epa", description="Disposal jurisdiction: 'us_epa', 'eu_standard', 'uk_wrap', 'india_cpcb'"),
    is_contaminated: bool = Form(False, description="Flag if waste item is soiled with grease, food, or chemicals"),
    current_user: Optional[UserProfile] = Depends(get_optional_current_user)
):
    """
    Analyzes an uploaded waste image.
    Executes Model B (multi-object detection) and Model A (fine-grained classification),
    evaluates contamination risks, and returns localized recycling instructions and EPA WARM metrics.
    """
    # 1. Validate File MIME Type
    content_type = file.content_type.lower() if file.content_type else "image/jpeg"
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{content_type}'. Allowed types: {settings.ALLOWED_IMAGE_TYPES}"
        )
        
    # 2. Read File Bytes & Validate Size
    try:
        try:
            contents = await file.read()
        except Exception:
            # Fallback to direct synchronous read on underlying SpooledTemporaryFile
            contents = file.file.read() if hasattr(file, "file") else b""
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {e}"
        )
        
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )
        
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB."
        )

    # 3. Execute Analysis Pipeline
    try:
        result = await pipeline_service.analyze_image(
            image_bytes=contents,
            filename=file.filename or "upload.jpg",
            location=location,
            is_contaminated=is_contaminated,
            current_user=current_user
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis pipeline error: {e}")
