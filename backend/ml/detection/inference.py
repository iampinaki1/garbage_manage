"""
Model B: Ultralytics YOLO Multi-Object Waste Detection Inference Service.
Requirements handled:
  - Detects multiple waste objects in a single image.
  - Returns bounding boxes (normalized and absolute pixels), class names, and confidence scores.
  - Produces cropped object ROIs for secondary classification.
  - Generates annotated images with visual bounding box overlays, labels, and color-coded tags.
  - Saves annotated images to static storage and returns accessible paths/base64 representations.
"""

import io
import sys
import time
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.ml.preprocessing.class_mapping import (
    CANONICAL_CATEGORIES,
    CANONICAL_TO_DISPLAY,
    CLASS_TO_ID,
    ID_TO_CLASS
)

DEFAULT_YOLO_WEIGHTS = ROOT / "trained_models" / "detection" / "waste_yolo.pt"
STATIC_ANNOTATED_DIR = ROOT / "backend" / "static" / "annotated"

# Distinct color palette for 9 canonical classes (Hex -> BGR)
CATEGORY_COLORS = {
    "organic_waste": (46, 139, 87),     # Sea Green
    "paper_waste": (205, 133, 63),     # Peru / Cardboard
    "plastic_waste": (30, 144, 255),   # Dodger Blue
    "metal_waste": (169, 169, 169),    # Dark Gray / Steel
    "glass_waste": (0, 191, 255),      # Deep Sky Blue
    "electronic_waste": (138, 43, 226),# Blue Violet
    "hazardous_waste": (220, 20, 60),  # Crimson Red
    "textile_waste": (218, 112, 214),  # Orchid
    "residual_waste": (105, 105, 105)  # Dim Gray
}

class YOLODetectorInference:
    """Production inference wrapper for Model B YOLO multi-object detector."""
    
    def __init__(
        self,
        weights_path: Optional[Union[str, Path]] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: Optional[str] = None
    ):
        self.weights_path = Path(weights_path) if weights_path else DEFAULT_YOLO_WEIGHTS
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        
        # Load weights: use custom trained weights if exists, else fallback to base pretrained
        if self.weights_path.exists():
            target_weights = str(self.weights_path)
        else:
            target_weights = "yolov8n.pt"
            print(f"Notice: Custom YOLO weights not found at {self.weights_path}. Using base {target_weights} as fallback.")
            
        self.model = YOLO(target_weights)
        self.device = device if device else ("0" if cv2.cuda.getCudaEnabledDeviceCount() > 0 or True else "cpu")
        STATIC_ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

    def detect(
        self,
        image_input: Union[str, Path, Image.Image, bytes, np.ndarray],
        return_crops: bool = True
    ) -> Dict[str, Any]:
        """
        Executes multi-object detection on an input image.
        Returns detected objects list and annotated image.
        """
        t0 = time.time()
        
        # 1. Parse Image Input to PIL Image and NumPy BGR
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
            
        img_w, img_h = pil_img.size
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # 2. Run YOLO Inference
        results = self.model.predict(
            source=np.array(pil_img),
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        detected_objects = []
        annotated_cv = cv_img.copy()
        
        if results and len(results) > 0:
            boxes = results[0].boxes
            for idx, box in enumerate(boxes):
                # Coordinates
                xyxy = box.xyxy[0].cpu().numpy().tolist() # [x1, y1, x2, y2]
                x1, y1, x2, y2 = [int(v) for v in xyxy]
                
                # Clip coordinates to image boundary
                x1 = max(0, min(img_w - 1, x1))
                y1 = max(0, min(img_h - 1, y1))
                x2 = max(x1 + 1, min(img_w, x2))
                y2 = max(y1 + 1, min(img_h, y2))
                
                conf = float(box.conf[0].cpu().numpy())
                cls_idx = int(box.cls[0].cpu().numpy())
                
                # Map to canonical name
                if cls_idx < len(CANONICAL_CATEGORIES):
                    canonical_name = CANONICAL_CATEGORIES[cls_idx]
                else:
                    # Model might use COCO names if running base fallback
                    model_names = getattr(self.model, "names", {})
                    raw_name = model_names.get(cls_idx, "residual_waste")
                    from backend.ml.preprocessing.class_mapping import map_raw_label
                    canonical_name, _ = map_raw_label(raw_name)
                    
                display_name = CANONICAL_TO_DISPLAY.get(canonical_name, canonical_name.replace("_", " ").title())
                
                # Normalized bounding box [ymin, xmin, ymax, xmax] in [0, 1]
                norm_box = [
                    round(y1 / img_h, 4),
                    round(x1 / img_w, 4),
                    round(y2 / img_h, 4),
                    round(x2 / img_w, 4)
                ]
                
                box_pixels = {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
                
                # Crop ROI if requested
                crop_pil = None
                if return_crops:
                    crop_pil = pil_img.crop((x1, y1, x2, y2))
                    
                detected_objects.append({
                    "object_id": idx + 1,
                    "category": canonical_name,
                    "category_name": display_name,
                    "confidence": round(conf, 4),
                    "box_normalized": norm_box,
                    "box_pixels": box_pixels,
                    "crop_pil": crop_pil
                })
                
                # Draw Visual Overlay
                color = CATEGORY_COLORS.get(canonical_name, (0, 255, 0))
                cv2.rectangle(annotated_cv, (x1, y1), (x2, y2), color, 3)
                
                label_text = f"{display_name} {conf*100:.1f}%"
                font_scale = max(0.5, img_w / 1200)
                thickness = max(1, int(img_w / 600))
                (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                
                # Draw text background pill
                text_y1 = max(0, y1 - th - baseline - 8)
                text_y2 = y1
                cv2.rectangle(annotated_cv, (x1, text_y1), (x1 + tw + 10, text_y2), color, -1)
                cv2.putText(
                    annotated_cv,
                    label_text,
                    (x1 + 5, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                    cv2.LINE_AA
                )
                
        annotated_pil = Image.fromarray(cv2.cvtColor(annotated_cv, cv2.COLOR_BGR2RGB))
        latency_ms = round((time.time() - t0) * 1000, 2)
        
        return {
            "total_detected": len(detected_objects),
            "detected_objects": detected_objects,
            "annotated_pil": annotated_pil,
            "image_size": [img_w, img_h],
            "latency_ms": latency_ms
        }

    def save_annotated_image(self, annotated_pil: Image.Image, filename: Optional[str] = None) -> Path:
        """Saves annotated PIL image to backend/static/annotated/."""
        if not filename:
            filename = f"annotated_{int(time.time()*1000)}.jpg"
        out_path = STATIC_ANNOTATED_DIR / filename
        annotated_pil.save(out_path, format="JPEG", quality=92)
        return out_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test YOLO Multi-Object Waste Detector")
    parser.add_argument("--image", type=str, required=True, help="Input image path")
    args = parser.parse_args()
    
    detector = YOLODetectorInference()
    res = detector.detect(args.image)
    print(f"Detected {res['total_detected']} objects in {res['latency_ms']} ms:")
    for obj in res["detected_objects"]:
        print(f"  Object #{obj['object_id']}: {obj['category_name']} ({obj['confidence']*100:.1f}%) at {obj['box_pixels']}")
    out = detector.save_annotated_image(res["annotated_pil"])
    print(f"Annotated image saved to: {out}")
