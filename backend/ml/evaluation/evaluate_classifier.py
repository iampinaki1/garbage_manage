"""
Evaluation Suite for Model A (Waste Image Classifier).
Requirements handled:
  - Evaluates trained model on unseen test split (datasets/processed/test_split.csv).
  - Calculates accuracy, precision, recall, and F1-score (macro and weighted).
  - Computes per-class classification report.
  - Generates and plots annotated Confusion Matrix heatmap.
  - Exports test_metrics.json for reporting and frontend visualization.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

import torch
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.classification.dataset import WasteDataset, get_val_transforms
from backend.ml.classification.model import WasteClassifier
from backend.ml.preprocessing.class_mapping import CANONICAL_CATEGORIES, CANONICAL_TO_DISPLAY

PROCESSED_DIR = ROOT / "datasets" / "processed"
TRAINED_MODELS_DIR = ROOT / "trained_models" / "classification"

def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list,
    output_path: Path
):
    """Plots and saves a formatted confusion matrix heatmap."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=[CANONICAL_TO_DISPLAY.get(c, c) for c in class_names],
        yticklabels=[CANONICAL_TO_DISPLAY.get(c, c) for c in class_names],
        cbar=True
    )
    plt.title("Model A: Waste Classification Confusion Matrix (Test Split)", fontsize=13, fontweight="bold")
    plt.ylabel("True Class", fontsize=11, fontweight="bold")
    plt.xlabel("Predicted Class", fontsize=11, fontweight="bold")
    plt.xticks(rotation=40, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"Confusion Matrix plot saved to: {output_path}")

def evaluate_model(
    checkpoint_path: Path = TRAINED_MODELS_DIR / "waste_classifier.pth",
    test_csv: Path = PROCESSED_DIR / "test_split.csv",
    batch_size: int = 32
) -> Dict[str, Any]:
    print("=" * 60)
    print("EVALUATING MODEL A ON UNSEEN TEST SPLIT")
    print(f"Checkpoint: {checkpoint_path}")
    print(f"Test Manifest: {test_csv}")
    print("=" * 60)
    
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {checkpoint_path}. Train the model first.")
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Inference Device: {device}")
    
    # 1. Load Model
    model = WasteClassifier.load_from_checkpoint(checkpoint_path, device=device)
    model.eval()
    
    # 2. Test DataLoader
    test_dataset = WasteDataset(test_csv, transform=get_val_transforms())
    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )
    print(f"Evaluating {len(test_dataset)} test samples across {len(test_loader)} batches...")
    
    # 3. Inference Loop
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for images, targets, _ in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())
            
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    
    # 4. Metrics Calculation
    acc = float(accuracy_score(all_targets, all_preds))
    
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        all_targets, all_preds, average="macro", zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        all_targets, all_preds, average="weighted", zero_division=0
    )
    
    # Determine unique labels present in evaluation
    present_labels = sorted(list(set(all_targets).union(set(all_preds))))
    present_names = [CANONICAL_CATEGORIES[i] for i in present_labels]
    
    # Per-class report
    clf_report = classification_report(
        all_targets,
        all_preds,
        labels=present_labels,
        target_names=present_names,
        output_dict=True,
        zero_division=0
    )
    
    # Confusion Matrix
    cm = confusion_matrix(all_targets, all_preds, labels=present_labels)
    
    # 5. Output Summary
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS (MODEL A):")
    print(f"  Test Accuracy        : {acc * 100:.2f}%")
    print(f"  Macro Precision      : {precision_macro:.4f}")
    print(f"  Macro Recall         : {recall_macro:.4f}")
    print(f"  Macro F1-Score       : {f1_macro:.4f}")
    print(f"  Weighted F1-Score    : {f1_weighted:.4f}")
    print("=" * 60)
    
    print("\nPer-Class Breakdown:")
    for name in present_names:
        stats = clf_report.get(name, {})
        print(f"  {name:<18}: Prec: {stats.get('precision', 0):.3f} | Rec: {stats.get('recall', 0):.3f} | F1: {stats.get('f1-score', 0):.3f} (N={stats.get('support', 0)})")
        
    # 6. Save Plots and Reports
    cm_path = TRAINED_MODELS_DIR / "confusion_matrix.png"
    plot_confusion_matrix(cm, present_names, cm_path)
    
    metrics_payload = {
        "model_path": str(checkpoint_path),
        "total_test_samples": int(len(all_targets)),
        "accuracy": round(acc, 4),
        "macro_metrics": {
            "precision": round(float(precision_macro), 4),
            "recall": round(float(recall_macro), 4),
            "f1_score": round(float(f1_macro), 4)
        },
        "weighted_metrics": {
            "precision": round(float(precision_weighted), 4),
            "recall": round(float(recall_weighted), 4),
            "f1_score": round(float(f1_weighted), 4)
        },
        "classification_report": clf_report,
        "confusion_matrix": cm.tolist(),
        "evaluated_classes": present_names
    }
    
    metrics_out = TRAINED_MODELS_DIR / "test_metrics.json"
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
        
    print(f"\nTest metrics exported to: {metrics_out}")
    return metrics_payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Model A Waste Classifier")
    parser.add_argument("--checkpoint", type=str, default=str(TRAINED_MODELS_DIR / "waste_classifier.pth"))
    parser.add_argument("--test-csv", type=str, default=str(PROCESSED_DIR / "test_split.csv"))
    args = parser.parse_args()
    
    evaluate_model(
        checkpoint_path=Path(args.checkpoint),
        test_csv=Path(args.test_csv)
    )

