"""
Training Pipeline for Model A (Waste Image Classifier).
Requirements handled:
  - Loads pretrained architecture (MobileNetV3-Small / EfficientNet-B0).
  - Fine-tunes using TrashNet and RealWaste dataset splits.
  - Applies weighted CrossEntropyLoss using Phase 2 balanced class weights.
  - Supports FP16 mixed precision acceleration on RTX 4050 GPU.
  - Evaluates validation accuracy and loss per epoch.
  - Saves best model checkpoint weights to trained_models/classification/waste_classifier.pth.
  - Generates and plots training & validation loss curves and accuracy charts.
  - Saves detailed JSON and CSV training logs.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import matplotlib
matplotlib.use("Agg") # Non-interactive backend for server/script rendering
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.classification.dataset import create_dataloaders
from backend.ml.classification.model import WasteClassifier
from backend.ml.preprocessing.class_mapping import CANONICAL_CATEGORIES, CLASS_TO_ID

PROCESSED_DIR = ROOT / "datasets" / "processed"
TRAINED_MODELS_DIR = ROOT / "trained_models" / "classification"

def get_class_weights_tensor(weights_path: Path, device: torch.device) -> torch.Tensor:
    """Loads balanced class weights from JSON and aligns them by category ID."""
    weights_tensor = torch.ones(len(CANONICAL_CATEGORIES), dtype=torch.float32)
    if weights_path.exists():
        with open(weights_path, "r", encoding="utf-8") as f:
            weights_dict = json.load(f)
        for cat_name, w in weights_dict.items():
            if cat_name in CLASS_TO_ID:
                idx = CLASS_TO_ID[cat_name]
                weights_tensor[idx] = float(w)
    return weights_tensor.to(device)

def train_one_epoch(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.cuda.amp.GradScaler,
    device: torch.device,
    use_amp: bool = True
) -> Tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, targets, _ in dataloader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        
        optimizer.zero_grad(set_to_none=True)
        
        with torch.cuda.amp.autocast(enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, targets)
            
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)
        
    epoch_loss = running_loss / max(1, total)
    epoch_acc = correct / max(1, total)
    return epoch_loss, epoch_acc

@torch.no_grad()
def validate(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
    use_amp: bool = True
) -> Tuple[float, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, targets, _ in dataloader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        
        with torch.cuda.amp.autocast(enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, targets)
            
        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)
        
    val_loss = running_loss / max(1, total)
    val_acc = correct / max(1, total)
    return val_loss, val_acc

def plot_training_history(history: List[Dict[str, Any]], output_path: Path):
    """Plots and exports loss curves and accuracy curves."""
    epochs = [h["epoch"] for h in history]
    train_losses = [h["train_loss"] for h in history]
    val_losses = [h["val_loss"] for h in history]
    train_accs = [h["train_acc"] * 100 for h in history]
    val_accs = [h["val_acc"] * 100 for h in history]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss Curve
    ax1.plot(epochs, train_losses, "b-o", label="Train Loss", linewidth=2)
    ax1.plot(epochs, val_losses, "r--s", label="Validation Loss", linewidth=2)
    ax1.set_title("Model A: Cross-Entropy Loss Curve", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend()
    
    # Accuracy Curve
    ax2.plot(epochs, train_accs, "b-o", label="Train Top-1 Accuracy", linewidth=2)
    ax2.plot(epochs, val_accs, "g--^", label="Validation Top-1 Accuracy", linewidth=2)
    ax2.set_title("Model A: Top-1 Accuracy Curve (%)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy (%)")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend()
    
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"Loss curves saved to: {output_path}")

def train_classifier(
    epochs: int = 10,
    batch_size: int = 32,
    lr: float = 3e-4,
    weight_decay: float = 1e-4,
    model_name: str = "mobilenet_v3_small",
    patience: int = 4
) -> Dict[str, Any]:
    print("=" * 60)
    print(f"TRAINING MODEL A: {model_name.upper()} WASTE CLASSIFIER")
    print(f"Parameters: Epochs={epochs}, BatchSize={batch_size}, LR={lr}")
    print("=" * 60)
    
    TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Device selection
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = torch.cuda.is_available()
    print(f"Hardware Device: {device} | Mixed Precision (AMP): {use_amp}")
    if use_amp:
        print(f"GPU Model: {torch.cuda.get_device_name(0)}")
        
    # 2. DataLoaders
    train_csv = PROCESSED_DIR / "train_split.csv"
    val_csv = PROCESSED_DIR / "val_split.csv"
    train_loader, val_loader = create_dataloaders(
        train_csv=train_csv,
        val_csv=val_csv,
        batch_size=batch_size,
        num_workers=0 # Set to 0 on Windows to avoid multi-processing socket overhead
    )
    print(f"Data batches: Train={len(train_loader)} batches ({len(train_loader.dataset)} images) | Val={len(val_loader)} batches ({len(val_loader.dataset)} images)")
    
    # 3. Model Architecture
    model = WasteClassifier(
        num_classes=len(CANONICAL_CATEGORIES),
        model_name=model_name,
        pretrained=True
    ).to(device)
    
    # 4. Criterion, Optimizer, Scheduler & Scaler
    weights_path = PROCESSED_DIR / "class_weights.json"
    class_weights = get_class_weights_tensor(weights_path, device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)
    
    # 5. Training Loop with Checkpointing
    best_val_loss = float("inf")
    best_val_acc = 0.0
    best_epoch = 0
    patience_counter = 0
    history = []
    
    checkpoint_path = TRAINED_MODELS_DIR / "waste_classifier.pth"
    t_start = time.time()
    
    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            scaler=scaler,
            device=device,
            use_amp=use_amp
        )
        val_loss, val_acc = validate(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
            device=device,
            use_amp=use_amp
        )
        scheduler.step()
        epoch_time = time.time() - t0
        
        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            best_val_acc = val_acc
            best_epoch = epoch
            patience_counter = 0
            model.save_weights(checkpoint_path)
            status_tag = "[BEST CHECKPOINT SAVED]"
        else:
            patience_counter += 1
            status_tag = ""
            
        print(f"Epoch {epoch:02d}/{epochs:02d} [{epoch_time:.1f}s] - Train Loss: {train_loss:.4f}, Train Acc: {train_acc*100:.2f}% | Val Loss: {val_loss:.4f}, Val Acc: {val_acc*100:.2f}% {status_tag}")
        
        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "learning_rate": float(scheduler.get_last_lr()[0]),
            "epoch_duration_sec": round(epoch_time, 2)
        })
        
        if patience_counter >= patience and epoch >= 5:
            print(f"\nEarly stopping triggered after {patience} epochs without validation loss improvement.")
            break
            
    total_training_time = time.time() - t_start
    print("=" * 60)
    print(f"Training Complete in {total_training_time:.1f} seconds.")
    print(f"Best Validation Loss: {best_val_loss:.4f} at Epoch {best_epoch} (Val Acc: {best_val_acc*100:.2f}%)")
    print(f"Best Model Saved to: {checkpoint_path}")
    print("=" * 60)
    
    # 6. Save Training History Logs and Curves
    log_json_path = TRAINED_MODELS_DIR / "training_log.json"
    log_csv_path = TRAINED_MODELS_DIR / "training_history.csv"
    loss_curve_path = TRAINED_MODELS_DIR / "loss_curve.png"
    
    summary = {
        "model_name": model_name,
        "total_epochs_trained": len(history),
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 4),
        "best_val_accuracy": round(best_val_acc, 4),
        "total_training_time_sec": round(total_training_time, 1),
        "device": str(device),
        "checkpoint_file": str(checkpoint_path.name),
        "history": history
    }
    with open(log_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    pd.DataFrame(history).to_csv(log_csv_path, index=False)
    plot_training_history(history, loss_curve_path)
    
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Model A Waste Classifier")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--model", type=str, default="mobilenet_v3_small", choices=["mobilenet_v3_small", "efficientnet_b0"])
    args = parser.parse_args()
    
    train_classifier(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        model_name=args.model
    )
