"""
Training and Fine-Tuning Pipeline for Model B (Ultralytics YOLO Multi-Object Detector).
Requirements handled:
  - Loads pretrained YOLOv8 (yolov8n.pt).
  - Trains/fine-tunes on converted TACO YOLO dataset (datasets/processed/yolo/data.yaml).
  - Uses RTX 4050 GPU (device=0) with mixed precision (amp=True).
  - Computes validation metrics: mAP50, mAP50-95, precision, and recall.
  - Exports trained weights to trained_models/detection/waste_yolo.pt.
  - Exports metrics report to trained_models/detection/detection_metrics.json.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent.parent
YOLO_DATA_YAML = ROOT / "datasets" / "processed" / "yolo" / "data.yaml"
TRAINED_MODELS_DIR = ROOT / "trained_models" / "detection"

def train_yolo_detector(
    epochs: int = 10,
    imgsz: int = 640,
    batch_size: int = 8,
    model_variant: str = "yolov8n.pt",
    device: str = "0"
) -> Dict[str, Any]:
    print("=" * 60)
    print(f"TRAINING MODEL B: {model_variant} MULTI-OBJECT DETECTOR")
    print(f"Dataset config: {YOLO_DATA_YAML}")
    print(f"Parameters: Epochs={epochs}, ImgSize={imgsz}, BatchSize={batch_size}")
    print("=" * 60)
    
    if not YOLO_DATA_YAML.exists():
        raise FileNotFoundError(f"YOLO data.yaml not found at: {YOLO_DATA_YAML}. Run coco_to_yolo.py first.")
        
    TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load pretrained YOLO model
    model = YOLO(model_variant)
    
    # Set Ultralytics config / runs directory safely inside project
    project_runs = ROOT / "trained_models" / "detection" / "runs"
    project_runs.mkdir(parents=True, exist_ok=True)
    
    # 2. Train on TACO YOLO dataset
    results = model.train(
        data=str(YOLO_DATA_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=device,
        project=str(project_runs),
        name="waste_yolo_run",
        exist_ok=True,
        amp=True,
        verbose=True,
        plots=True
    )
    
    # 3. Validation & Metrics
    val_results = model.val(data=str(YOLO_DATA_YAML), device=device)
    
    map50 = float(val_results.box.map50)
    map50_95 = float(val_results.box.map)
    precision = float(val_results.box.mp)
    recall = float(val_results.box.mr)
    
    print("\n" + "=" * 60)
    print("MODEL B (YOLOv8) VALIDATION METRICS:")
    print(f"  mAP@50     : {map50:.4f} ({map50 * 100:.2f}%)")
    print(f"  mAP@50-95  : {map50_95:.4f} ({map50_95 * 100:.2f}%)")
    print(f"  Precision  : {precision:.4f}")
    print(f"  Recall     : {recall:.4f}")
    print("=" * 60)
    
    # 4. Copy best weights to canonical path
    best_pt = project_runs / "waste_yolo_run" / "weights" / "best.pt"
    dest_pt = TRAINED_MODELS_DIR / "waste_yolo.pt"
    if best_pt.exists():
        shutil.copy2(best_pt, dest_pt)
        print(f"Best detector checkpoint saved to: {dest_pt}")
    else:
        # Fallback to model save
        model.save(str(dest_pt))
        print(f"Model saved to: {dest_pt}")
        
    # 5. Export detection metrics JSON
    metrics_payload = {
        "model_architecture": model_variant,
        "epochs_trained": epochs,
        "image_size": imgsz,
        "batch_size": batch_size,
        "mAP50": round(map50, 4),
        "mAP50_95": round(map50_95, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "weights_path": str(dest_pt),
        "device": str(device)
    }
    
    metrics_file = TRAINED_MODELS_DIR / "detection_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
        
    print(f"Detection metrics exported to: {metrics_file}")
    return metrics_payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Model B YOLO Waste Detector")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--variant", type=str, default="yolov8n.pt", help="YOLO variant")
    args = parser.parse_args()
    
    train_yolo_detector(
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch_size=args.batch,
        model_variant=args.variant
    )

