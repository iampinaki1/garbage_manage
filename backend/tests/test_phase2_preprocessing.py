"""
Phase 2: Dataset Preprocessing, Class Mapping & Bounding Box Pipeline Tests
"""
import sys
import json
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.preprocessing.class_mapping import (
    map_raw_label,
    CANONICAL_CATEGORIES,
    CLASS_TO_ID,
    ID_TO_CLASS,
    TRASHNET_MAP,
    REALWASTE_MAP,
    TACO_MAP
)
from backend.ml.detection.coco_to_yolo import coco_to_yolo_bbox

PROCESSED_DIR = ROOT / "datasets" / "processed"
YOLO_DIR = PROCESSED_DIR / "yolo"

def test_canonical_categories():
    assert len(CANONICAL_CATEGORIES) == 9
    assert len(CLASS_TO_ID) == 9
    assert len(ID_TO_CLASS) == 9
    for idx, cat in enumerate(CANONICAL_CATEGORIES):
        assert CLASS_TO_ID[cat] == idx
        assert ID_TO_CLASS[idx] == cat

def test_trashnet_mapping():
    for raw, expected in TRASHNET_MAP.items():
        canonical, cat_id = map_raw_label(raw, source="trashnet")
        assert canonical == expected
        assert 0 <= cat_id < 9

def test_realwaste_mapping():
    for raw, expected in REALWASTE_MAP.items():
        canonical, cat_id = map_raw_label(raw, source="realwaste")
        assert canonical == expected
        assert 0 <= cat_id < 9

def test_taco_mapping():
    for raw, expected in TACO_MAP.items():
        canonical, cat_id = map_raw_label(raw, source="taco")
        assert canonical == expected
        assert 0 <= cat_id < 9

def test_mapping_fallback():
    # Test keywords fallback
    cat, cid = map_raw_label("random plastic container")
    assert cat == "plastic_waste"
    cat, cid = map_raw_label("old cardboard shipping crate")
    assert cat == "paper_waste"
    cat, cid = map_raw_label("vegetable scraps and banana peel")
    assert cat == "organic_waste"
    cat, cid = map_raw_label("unknown mystery object 12345")
    assert cat == "residual_waste"

def test_coco_to_yolo_bbox_normalization():
    # Box: x=100, y=100, w=200, h=200 in image of 1000x1000
    # Center = (200, 200) -> norm center = (0.2, 0.2), norm w/h = (0.2, 0.2)
    nx, ny, nw, nh = coco_to_yolo_bbox([100, 100, 200, 200], 1000, 1000)
    assert nx == 0.2
    assert ny == 0.2
    assert nw == 0.2
    assert nh == 0.2
    
    # Boundary clipping test
    nx, ny, nw, nh = coco_to_yolo_bbox([-50, -50, 1500, 1500], 1000, 1000)
    assert 0.0 <= nx <= 1.0
    assert 0.0 <= ny <= 1.0
    assert 0.0 <= nw <= 1.0
    assert 0.0 <= nh <= 1.0

def test_split_files_exist_and_non_empty():
    train_csv = PROCESSED_DIR / "train_split.csv"
    val_csv = PROCESSED_DIR / "val_split.csv"
    test_csv = PROCESSED_DIR / "test_split.csv"
    
    assert train_csv.exists()
    assert val_csv.exists()
    assert test_csv.exists()
    
    train_df = pd.read_csv(train_csv)
    val_df = pd.read_csv(val_csv)
    test_df = pd.read_csv(test_csv)
    
    assert len(train_df) > 1000
    assert len(val_df) > 100
    assert len(test_df) > 100
    
    # Check 80/10/10 ratio approximately
    total = len(train_df) + len(val_df) + len(test_df)
    train_pct = len(train_df) / total
    assert 0.75 <= train_pct <= 0.85

def test_zero_data_leakage_between_splits():
    train_df = pd.read_csv(PROCESSED_DIR / "train_split.csv")
    val_df = pd.read_csv(PROCESSED_DIR / "val_split.csv")
    test_df = pd.read_csv(PROCESSED_DIR / "test_split.csv")
    
    train_hashes = set(train_df["sha256"])
    val_hashes = set(val_df["sha256"])
    test_hashes = set(test_df["sha256"])
    
    assert len(train_hashes.intersection(val_hashes)) == 0, "Train and Val share duplicate hashes"
    assert len(train_hashes.intersection(test_hashes)) == 0, "Train and Test share duplicate hashes"
    assert len(val_hashes.intersection(test_hashes)) == 0, "Val and Test share duplicate hashes"

def test_class_weights_validity():
    weights_path = PROCESSED_DIR / "class_weights.json"
    assert weights_path.exists()
    with open(weights_path, "r", encoding="utf-8") as f:
        weights = json.load(f)
    assert len(weights) >= 6
    for cls, w in weights.items():
        assert w > 0.0, f"Class weight for {cls} must be positive, got {w}"

def test_yolo_dataset_structure_and_yaml():
    yaml_file = YOLO_DIR / "data.yaml"
    assert yaml_file.exists()
    with open(yaml_file, "r", encoding="utf-8") as f:
        import yaml
        cfg = yaml.safe_load(f)
    assert cfg["nc"] == 9
    assert len(cfg["names"]) == 9
    assert (YOLO_DIR / "images" / "train").exists()
    assert (YOLO_DIR / "images" / "val").exists()
    assert (YOLO_DIR / "labels" / "train").exists()
    assert (YOLO_DIR / "labels" / "val").exists()
    
    # Check that labels contain valid numbers
    label_files = list((YOLO_DIR / "labels").rglob("*.txt"))
    assert len(label_files) > 0
    for lf in label_files[:10]:
        content = lf.read_text(encoding="utf-8").strip()
        if content:
            for line in content.splitlines():
                parts = line.split()
                assert len(parts) == 5
                cid = int(parts[0])
                assert 0 <= cid < 9
                coords = [float(p) for p in parts[1:]]
                for c in coords:
                    assert 0.0 <= c <= 1.0

