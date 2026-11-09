"""
Phase 3: Model A Architecture, Dataset Loading & Inference Pipeline Tests
"""
import sys
import tempfile
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.classification.dataset import WasteDataset, get_train_transforms, get_val_transforms
from backend.ml.classification.model import WasteClassifier
from backend.ml.classification.inference import WasteClassifierInference
from backend.ml.preprocessing.class_mapping import CANONICAL_CATEGORIES

PROCESSED_DIR = ROOT / "datasets" / "processed"

def test_train_and_val_transforms():
    img = Image.new("RGB", (300, 300), color=(128, 64, 32))
    train_tf = get_train_transforms()
    val_tf = get_val_transforms()
    
    t_train = train_tf(img)
    t_val = val_tf(img)
    
    assert isinstance(t_train, torch.Tensor)
    assert t_train.shape == (3, 224, 224)
    assert isinstance(t_val, torch.Tensor)
    assert t_val.shape == (3, 224, 224)

def test_waste_dataset_loading():
    train_csv = PROCESSED_DIR / "train_split.csv"
    assert train_csv.exists(), "train_split.csv should exist"
    
    ds = WasteDataset(train_csv, transform=get_val_transforms())
    assert len(ds) > 1000
    
    img_tensor, cat_id, cat_name = ds[0]
    assert img_tensor.shape == (3, 224, 224)
    assert 0 <= cat_id < len(CANONICAL_CATEGORIES)
    assert cat_name in CANONICAL_CATEGORIES

def test_waste_classifier_architecture():
    model = WasteClassifier(
        num_classes=9,
        model_name="mobilenet_v3_small",
        pretrained=False # False for fast unit testing
    )
    dummy_input = torch.randn(2, 3, 224, 224)
    logits = model(dummy_input)
    
    assert logits.shape == (2, 9), f"Expected shape (2, 9), got {logits.shape}"
    
    probs = model.predict_proba(dummy_input)
    assert probs.shape == (2, 9)
    # Check probabilities sum to 1.0
    sum_p = probs.sum(dim=1).detach().numpy()
    np.testing.assert_allclose(sum_p, [1.0, 1.0], rtol=1e-5)

def test_model_save_and_load_roundtrip():
    model = WasteClassifier(num_classes=9, model_name="mobilenet_v3_small", pretrained=False)
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        
    try:
        model.save_weights(tmp_path)
        assert tmp_path.exists()
        
        loaded = WasteClassifier.load_from_checkpoint(tmp_path, device=torch.device("cpu"))
        model.eval()
        dummy_input = torch.randn(1, 3, 224, 224)
        out_orig = model(dummy_input)
        out_loaded = loaded(dummy_input)
        torch.testing.assert_close(out_orig, out_loaded)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def test_inference_service_with_synthetic_model():
    # Save a temporary checkpoint
    model = WasteClassifier(num_classes=9, model_name="mobilenet_v3_small", pretrained=False)
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        
    try:
        model.save_weights(tmp_path)
        service = WasteClassifierInference(checkpoint_path=tmp_path, device="cpu", min_confidence=0.1)
        assert service.is_ready()
        
        test_img = Image.new("RGB", (250, 250), color=(50, 150, 250))
        res = service.predict(test_img)
        
        assert "category" in res
        assert "confidence" in res
        assert "all_probabilities" in res
        assert len(res["all_probabilities"]) == 9
        assert "latency_ms" in res
        assert res["latency_ms"] > 0
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
