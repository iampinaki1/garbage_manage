"""
Unified Waste Analysis Pipeline Coordinator.
Orchestrates:
1. Image validation and preprocessing.
2. Model B YOLO multi-object detection (bounding boxes & visual overlays).
3. Model A MobileNetV3 classification on detected ROIs (or full image if single item).
4. Recommendation Engine localized guidance and EPA/EEA environmental impact calculation.
5. Persistent logging to MongoDB/in-memory store.
"""

import io
import time
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

from PIL import Image

from backend.app.core.config import settings
from backend.app.database.connection import db_manager
from backend.app.models.schemas import (
    AnalyzeResponse,
    AnalysisSummary,
    DetectedObject,
    BoundingBox,
    ContaminationInfo,
    EnvironmentalImpactInfo,
    UserProfile
)
from backend.ml.classification.inference import WasteClassifierInference
from backend.ml.detection.inference import YOLODetectorInference
from backend.recommendations.recommendation_engine import get_recommendation_engine, LOCATION_PROFILES

logger = logging.getLogger(__name__)

class PipelineService:
    """Production service coordinating detection, classification, recommendations, and persistence."""

    def __init__(self):
        self._classifier: Optional[WasteClassifierInference] = None
        self._detector: Optional[YOLODetectorInference] = None
        self._recommendation_engine = get_recommendation_engine()

    @property
    def classifier(self) -> WasteClassifierInference:
        if self._classifier is None:
            weights = settings.CLASSIFIER_WEIGHTS if settings.CLASSIFIER_WEIGHTS.exists() else None
            self._classifier = WasteClassifierInference(checkpoint_path=weights)
        return self._classifier

    @property
    def detector(self) -> YOLODetectorInference:
        if self._detector is None:
            weights = settings.DETECTOR_WEIGHTS if settings.DETECTOR_WEIGHTS.exists() else None
            self._detector = YOLODetectorInference(weights_path=weights, conf_threshold=0.15)
        return self._detector

    def get_model_health_status(self) -> Dict[str, Any]:
        """Reports loaded model availability and weight statuses."""
        classifier_ready = settings.CLASSIFIER_WEIGHTS.exists()
        detector_ready = settings.DETECTOR_WEIGHTS.exists()
        csv_ready = settings.RECYCLING_CSV.exists()
        return {
            "model_a_classifier": {
                "name": "MobileNetV3-Small WasteClassifier",
                "weights_exist": classifier_ready,
                "weights_path": str(settings.CLASSIFIER_WEIGHTS),
                "status": "ready" if classifier_ready else "fallback"
            },
            "model_b_detector": {
                "name": "YOLOv8n Multi-Object Detector",
                "weights_exist": detector_ready,
                "weights_path": str(settings.DETECTOR_WEIGHTS),
                "status": "ready" if detector_ready else "fallback"
            },
            "recommendation_engine": {
                "name": "RecyclingRecommendationEngine",
                "database_loaded": len(self._recommendation_engine.database) > 0,
                "item_count": len(self._recommendation_engine.database),
                "status": "ready" if csv_ready else "fallback"
            }
        }

    async def analyze_image(
        self,
        image_bytes: bytes,
        filename: str = "upload.jpg",
        location: str = "us_epa",
        is_contaminated: bool = False,
        current_user: Optional[UserProfile] = None
    ) -> AnalyzeResponse:
        """
        Executes end-to-end intelligent waste segregation pipeline.
        """
        t0 = time.time()
        analysis_id = str(uuid.uuid4())
        timestamp_iso = datetime.now(timezone.utc).isoformat()
        
        # 1. Validate Image Bytes & Open PIL Image
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid image format or corrupted file: {e}")
            
        img_w, img_h = pil_img.size
        
        # 2. Save Original Upload Image to Static Directory
        clean_ext = Path(filename).suffix.lower() if Path(filename).suffix else ".jpg"
        if clean_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            clean_ext = ".jpg"
        upload_fname = f"orig_{analysis_id[:8]}_{int(time.time())}{clean_ext}"
        upload_path = settings.UPLOADS_DIR / upload_fname
        pil_img.save(upload_path, quality=90)
        image_url = f"/static/uploads/{upload_fname}"

        # 3. Execute Model B YOLO Multi-Object Detection
        detection_res = self.detector.detect(pil_img, return_crops=True)
        detected_raw = detection_res.get("detected_objects", [])
        
        detections: List[DetectedObject] = []
        annotated_pil = detection_res.get("annotated_pil", pil_img)
        
        # 4. Process Detections
        if detected_raw:
            for idx, raw_obj in enumerate(detected_raw):
                cat = raw_obj["category"]
                conf = float(raw_obj["confidence"])
                crop = raw_obj.get("crop_pil")
                
                # Enrich with Model A classifier on crop ROI
                matched_label = raw_obj.get("category_name", cat)
                if crop is not None:
                    try:
                        cls_res = self.classifier.predict(crop)
                        # If classifier has strong confidence on the crop, use it to enrich
                        if cls_res.get("is_confident") and cls_res["confidence"] > 0.5:
                            cat = cls_res["category"]
                            conf = max(conf, float(cls_res["confidence"]))
                            matched_label = cls_res.get("category_name", matched_label)
                    except Exception as err:
                        logger.warning(f"Crop classification fallback: {err}")

                # Query Recommendation Engine
                rec = self._recommendation_engine.get_recommendation(
                    category=cat,
                    query_item=matched_label,
                    location=location,
                    is_contaminated=is_contaminated
                )
                
                # Format bounding box
                bx = raw_obj["box_pixels"]
                bbox_model = BoundingBox(
                    x1=bx["x1"], y1=bx["y1"], x2=bx["x2"], y2=bx["y2"],
                    width=bx["width"], height=bx["height"]
                )
                
                detections.append(
                    DetectedObject(
                        object_id=idx + 1,
                        category=rec["category"],
                        category_display=rec["category_display"],
                        matched_item=rec["matched_item"],
                        material=rec["material"],
                        confidence=round(conf, 4),
                        is_recyclable=rec["is_recyclable"],
                        is_conditional=rec["is_conditional"],
                        recyclability_status=rec["recyclability_status"],
                        recommended_bin=rec["recommended_bin"],
                        recycling_method=rec["recycling_method"],
                        preparation_instructions=rec["preparation_instructions"],
                        disposal_instructions=rec["disposal_instructions"],
                        box_pixels=bbox_model,
                        box_normalized=raw_obj.get("box_normalized"),
                        contamination_assessment=ContaminationInfo(**rec["contamination_assessment"]),
                        environmental_impact=EnvironmentalImpactInfo(**rec["environmental_impact"])
                    )
                )
        else:
            # Fallback: No bounding boxes found by YOLO -> Run Model A on the entire image
            cls_res = self.classifier.predict(pil_img)
            cat = cls_res["category"]
            if cat == "uncertain":
                probs = cls_res.get("all_probabilities", {})
                cat = max(probs, key=probs.get) if probs else "residual_waste"
            conf = float(cls_res["confidence"])
            matched_label = cls_res.get("category_name", cat)
            
            rec = self._recommendation_engine.get_recommendation(
                category=cat,
                query_item=matched_label,
                location=location,
                is_contaminated=is_contaminated
            )
            
            bbox_model = BoundingBox(x1=0, y1=0, x2=img_w, y2=img_h, width=img_w, height=img_h)
            detections.append(
                DetectedObject(
                    object_id=1,
                    category=rec["category"],
                    category_display=rec["category_display"],
                    matched_item=rec["matched_item"],
                    material=rec["material"],
                    confidence=round(conf, 4),
                    is_recyclable=rec["is_recyclable"],
                    is_conditional=rec["is_conditional"],
                    recyclability_status=rec["recyclability_status"],
                    recommended_bin=rec["recommended_bin"],
                    recycling_method=rec["recycling_method"],
                    preparation_instructions=rec["preparation_instructions"],
                    disposal_instructions=rec["disposal_instructions"],
                    box_pixels=bbox_model,
                    box_normalized=[0.5, 0.5, 1.0, 1.0],
                    contamination_assessment=ContaminationInfo(**rec["contamination_assessment"]),
                    environmental_impact=EnvironmentalImpactInfo(**rec["environmental_impact"])
                )
            )

        # 5. Save Annotated Image
        annotated_fname = f"annotated_{analysis_id[:8]}_{int(time.time())}.jpg"
        annotated_path = settings.ANNOTATED_DIR / annotated_fname
        annotated_pil.save(annotated_path, format="JPEG", quality=90)
        annotated_image_url = f"/static/annotated/{annotated_fname}"

        # 6. Aggregate Metrics & Recyclability
        total_co2 = round(sum(d.environmental_impact.estimated_co2_saved_kg for d in detections), 4)
        total_energy = round(sum(d.environmental_impact.estimated_energy_saved_kwh for d in detections), 4)
        total_weight = round(sum(d.environmental_impact.assumed_weight_kg for d in detections), 4)
        
        recyclable_count = sum(1 for d in detections if d.is_recyclable)
        conditional_count = sum(1 for d in detections if d.is_conditional)
        total_items = len(detections)
        
        if recyclable_count == total_items:
            overall_status = "Recyclable"
        elif recyclable_count > 0 or conditional_count > 0:
            overall_status = "Partially Recyclable"
        else:
            overall_status = "Non-Recyclable"

        primary_cat = detections[0].category if detections else "residual_waste"
        primary_display = detections[0].category_display if detections else "Residual Waste"

        latency_ms = round((time.time() - t0) * 1000, 2)

        summary = AnalysisSummary(
            total_objects_detected=total_items,
            primary_category=primary_cat,
            primary_category_display=primary_display,
            overall_recyclability=overall_status,
            total_co2_saved_kg=total_co2,
            total_energy_saved_kwh=total_energy,
            inference_latency_ms=latency_ms
        )

        total_impact = EnvironmentalImpactInfo(
            estimated_co2_saved_kg=total_co2,
            estimated_energy_saved_kwh=total_energy,
            assumed_weight_kg=total_weight,
            disclaimer="Cumulative estimates based on published EPA WARM v15 and EEA conversion factors.",
            reference_source="EPA WARM v15 / EEA Waste Directives"
        )

        response = AnalyzeResponse(
            analysis_id=analysis_id,
            timestamp=timestamp_iso,
            location_profile=location,
            image_url=image_url,
            annotated_image_url=annotated_image_url,
            summary=summary,
            detections=detections,
            total_environmental_impact=total_impact
        )

        # 7. Persist to MongoDB (or In-Memory store)
        doc = response.model_dump()
        if isinstance(current_user, UserProfile):
            doc["user_id"] = current_user.id
            doc["user_username"] = current_user.username
        else:
            doc["user_id"] = None
            doc["user_username"] = "anonymous"
        
        try:
            analyses_col = db_manager.get_collection("analyses")
            await analyses_col.insert_one(doc)
        except Exception as e:
            logger.error(f"Failed to persist analysis record: {e}")

        return response


# Global pipeline singleton
pipeline_service = PipelineService()
