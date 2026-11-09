"""
Model A: Waste Image Classification Inference Service.
Requirements handled:
  - Real-time inference on new/uploaded images.
  - Returns canonical class name, display name, category ID, and confidence score.
  - Provides full class probability distribution.
  - Implements confidence threshold gating (marks prediction as uncertain if below threshold).
  - Handles various input types (file path, PIL Image, bytes, numpy array).
"""

import io
import json
import time
from pathlib import Path
from typing import Union, Dict, Any, Optional

import torch
import numpy as np
from PIL import Image

import sys
ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.classification.dataset import get_val_transforms
from backend.ml.classification.model import WasteClassifier
from backend.ml.preprocessing.class_mapping import (
    CANONICAL_CATEGORIES,
    CANONICAL_TO_DISPLAY,
    CLASS_TO_ID,
    ID_TO_CLASS
)

DEFAULT_CHECKPOINT = ROOT / "trained_models" / "classification" / "waste_classifier.pth"
DEFAULT_CONFIDENCE_THRESHOLD = 0.40

class WasteClassifierInference:
    """Production inference wrapper for Model A waste classifier."""
    
    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD
    ):
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else DEFAULT_CHECKPOINT
        self.min_confidence = min_confidence
        
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
        self.transform = get_val_transforms()
        self.model: Optional[WasteClassifier] = None
        self._load_model()

    def _load_model(self):
        if not self.checkpoint_path.exists():
            print(f"Warning: Model checkpoint not found at {self.checkpoint_path}. Model will remain uninitialized until trained.")
            return
            
        self.model = WasteClassifier.load_from_checkpoint(self.checkpoint_path, device=self.device)
        self.model.eval()

    def is_ready(self) -> bool:
        return self.model is not None

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, bytes, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Runs waste classification on an input image.
        Returns detailed prediction dictionary.
        """
        if not self.is_ready():
            raise RuntimeError(f"Classifier is not loaded. Model weights missing at: {self.checkpoint_path}")
            
        t0 = time.time()
        
        # 1. Parse Image Input
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
            
        # 2. Preprocess
        tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        
        # 3. Predict Probabilities
        with torch.no_grad():
            outputs = self.model(tensor)
            probs = torch.softmax(outputs, dim=1).squeeze(0).cpu().numpy()
            
        top_idx = int(np.argmax(probs))
        top_conf = float(probs[top_idx])
        top_category = ID_TO_CLASS.get(top_idx, "residual_waste")
        display_name = CANONICAL_TO_DISPLAY.get(top_category, "Residual Waste")
        
        # 4. Check confidence threshold
        is_confident = top_conf >= self.min_confidence
        
        # 5. Full probability breakdown
        all_probs = {
            ID_TO_CLASS[i]: round(float(probs[i]), 4)
            for i in range(len(CANONICAL_CATEGORIES))
        }
        
        latency_ms = round((time.time() - t0) * 1000, 2)
        
        return {
            "category": top_category if is_confident else "uncertain",
            "category_name": display_name if is_confident else "Uncertain / Low Confidence",
            "category_id": top_idx if is_confident else -1,
            "confidence": round(top_conf, 4),
            "is_confident": is_confident,
            "min_confidence_threshold": self.min_confidence,
            "all_probabilities": all_probs,
            "latency_ms": latency_ms
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Waste Classifier Inference")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--checkpoint", type=str, default=str(DEFAULT_CHECKPOINT))
    args = parser.parse_args()
    
    engine = WasteClassifierInference(checkpoint_path=args.checkpoint)
    res = engine.predict(args.image)
    print("\n--- INFERENCE RESULT ---")
    print(json.dumps(res, indent=2))

