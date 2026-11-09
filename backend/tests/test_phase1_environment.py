"""
Phase 1: Environment, Dependencies & Dataset Scaffolding Tests
"""
import sys
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent

def test_python_version():
    assert sys.version_info >= (3, 10), "Python version must be >= 3.10"

def test_pytorch_installation():
    import torch
    assert torch.__version__ is not None
    # Test tensor allocation and device fallback
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    x = torch.tensor([1.0, 2.0, 3.0], device=device)
    assert x.sum().item() == 6.0

def test_vision_and_ml_libraries():
    import torchvision
    import cv2
    import PIL.Image
    import sklearn
    import pandas
    import numpy
    
    assert torchvision.__version__ is not None
    assert cv2.__version__ is not None
    assert numpy.__version__ is not None

def test_ultralytics_yolo():
    import ultralytics
    from ultralytics import YOLO
    assert ultralytics.__version__ is not None

def test_backend_and_db_libraries():
    import fastapi
    import uvicorn
    import pydantic
    import pymongo
    import motor
    import jwt
    import passlib
    
    assert fastapi.__version__ is not None
    assert pydantic.__version__ is not None

def test_directory_structure():
    required_dirs = [
        ROOT / "backend" / "app" / "api",
        ROOT / "backend" / "app" / "core",
        ROOT / "backend" / "app" / "database",
        ROOT / "backend" / "app" / "models",
        ROOT / "backend" / "app" / "recommendations",
        ROOT / "backend" / "app" / "services",
        ROOT / "backend" / "app" / "utils",
        ROOT / "backend" / "ml" / "classification",
        ROOT / "backend" / "ml" / "detection",
        ROOT / "backend" / "ml" / "preprocessing",
        ROOT / "backend" / "ml" / "training",
        ROOT / "backend" / "ml" / "evaluation",
        ROOT / "backend" / "tests",
        ROOT / "datasets" / "trashnet",
        ROOT / "datasets" / "realwaste",
        ROOT / "datasets" / "taco",
        ROOT / "trained_models" / "classification",
        ROOT / "trained_models" / "detection",
        ROOT / "scripts",
        ROOT / "docs"
    ]
    for d in required_dirs:
        assert d.exists(), f"Required directory {d} does not exist"

def test_config_files():
    assert (ROOT / ".env.example").exists()
    assert (ROOT / ".env").exists()
    assert (ROOT / ".gitignore").exists()
    assert (ROOT / "backend" / "requirements.txt").exists()

def test_taco_annotations():
    ann_path = ROOT / "datasets" / "taco" / "annotations.json"
    assert ann_path.exists(), "TACO annotations.json should exist"
    with open(ann_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "categories" in data
    assert "images" in data
    assert "annotations" in data
    assert len(data["categories"]) == 60

def test_trashnet_images_present():
    trashnet_dir = ROOT / "datasets" / "trashnet"
    classes = [d.name for d in trashnet_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    expected_classes = {"cardboard", "glass", "metal", "paper", "plastic", "trash"}
    assert expected_classes.issubset(set(classes)), f"TrashNet classes mismatch: {classes}"
    total_imgs = sum(len(list(d.glob("*.jpg"))) for d in trashnet_dir.iterdir() if d.is_dir())
    assert total_imgs > 2000, f"Expected >2000 TrashNet images, got {total_imgs}"

