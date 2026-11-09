"""
Phase 4: Model B (Ultralytics YOLO Detection) Tests
"""
import sys
from pathlib import Path
import yaml
import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.detection.coco_to_yolo import coco_to_yolo_bbox
from backend.ml.detection.inference import YOLODetectorInference
from backend.ml.preprocessing.class_mapping import CANONICAL_CATEGORIES

YOLO_DIR = ROOT / "datasets" / "processed" / "yolo"

def test_coco_bbox_conversion():
    # Absolute box [100, 200, 300, 400] on image 1000x1000
    # Center = (100 + 150 = 250, 200 + 200 = 400) -> norm = (0.25, 0.40, 0.30, 0.40)
    nx, ny, nw, nh = coco_to_yolo_bbox([100, 200, 300, 400], 1000, 1000)
    assert nx == 0.25
    assert ny == 0.40
    assert nw == 0.30
    assert nh == 0.40

def test_yolo_data_yaml_descriptor():
    yaml_file = YOLO_DIR / "data.yaml"
    assert yaml_file.exists(), "data.yaml should exist"
    with open(yaml_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg["nc"] == 9
    assert len(cfg["names"]) == 9
    for i in range(9):
        assert i in cfg["names"]
        assert cfg["names"][i] == CANONICAL_CATEGORIES[i]

def test_yolo_dataset_files_presence():
    train_images = list((YOLO_DIR / "images" / "train").glob("*.jpg"))
    val_images = list((YOLO_DIR / "images" / "val").glob("*.jpg"))
    train_labels = list((YOLO_DIR / "labels" / "train").glob("*.txt"))
    val_labels = list((YOLO_DIR / "labels" / "val").glob("*.txt"))
    
    assert len(train_images) > 0
    assert len(val_images) > 0
    assert len(train_labels) == len(train_images)
    assert len(val_labels) == len(val_images)

def test_yolo_detector_inference_on_synthetic_image():
    detector = YOLODetectorInference()
    
    # Create test image with shapes
    test_img = Image.new("RGB", (640, 640), color=(200, 200, 200))
    res = detector.detect(test_img, return_crops=True)
    
    assert "total_detected" in res
    assert "detected_objects" in res
    assert "annotated_pil" in res
    assert "latency_ms" in res
    assert res["latency_ms"] > 0
    assert isinstance(res["annotated_pil"], Image.Image)

def test_save_annotated_image():
    detector = YOLODetectorInference()
    test_img = Image.new("RGB", (400, 400), color=(100, 150, 200))
    res = detector.detect(test_img)
    
    out_file = detector.save_annotated_image(res["annotated_pil"], filename="test_annotated.jpg")
    assert out_file.exists()
    assert out_file.stat().st_size > 0
    if out_file.exists():
        out_file.unlink() # Cleanup test file

