"""
Dataset Split & Stratification Module.
Requirements handled:
  1. Creates stratified 80/10/10 Train, Validation, and Test splits.
  2. Prevents data leakage between splits (quarantines duplicates using content hashes).
  3. Preserves original dataset labels alongside canonical categories.
  4. Calculates balanced class weights to mitigate class imbalance.
  5. Configures standard image normalization (224x224, ImageNet mean/std) and augmentation pipelines.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROCESSED_DIR = ROOT / "datasets" / "processed"

def generate_splits(
    metadata_csv: Path = PROCESSED_DIR / "dataset_metadata.csv",
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    print("=" * 60)
    print("GENERATING LEAK-FREE STRATIFIED DATASET SPLITS")
    print(f"Ratios: Train {train_ratio*100:.0f}%, Val {val_ratio*100:.0f}%, Test {test_ratio*100:.0f}%")
    print("=" * 60)
    
    if not metadata_csv.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_csv}. Run inspect_datasets.py first.")
        
    df = pd.read_csv(metadata_csv)
    print(f"Total entries loaded: {len(df)}")
    
    # 1. Quarantine corrupted and duplicate images to prevent data leakage
    clean_df = df[(df["is_valid"] == True) & (df["is_duplicate"] == False)].copy()
    print(f"Clean, unique samples available for splitting: {len(clean_df)}")
    
    if clean_df.empty:
        raise ValueError("No valid unique images found to create splits!")
        
    # Filter classes with at least 3 samples for stratified splitting, or fallback
    class_counts = clean_df["canonical_category"].value_counts()
    print("\nClass distribution in clean dataset:")
    for cat, count in class_counts.items():
        print(f"  {cat:<18}: {count} samples")
        
    # Group rare classes if necessary (< 3 samples)
    stratify_col = clean_df["canonical_category"]
    rare_classes = class_counts[class_counts < 3].index.tolist()
    if rare_classes:
        print(f"Note: Rare classes (< 3 samples): {rare_classes}")
        stratify_col = clean_df["canonical_category"].apply(lambda c: "rare_group" if c in rare_classes else c)
        
    # 2. Stratified Train (80%) vs Temp (20%)
    temp_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        clean_df,
        test_size=temp_ratio,
        stratify=stratify_col,
        random_state=random_seed
    )
    
    # 3. Stratified Val (50% of Temp = 10%) vs Test (50% of Temp = 10%)
    val_ratio_in_temp = val_ratio / temp_ratio
    temp_stratify = temp_df["canonical_category"].apply(lambda c: "rare_group" if c in rare_classes else c)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1.0 - val_ratio_in_temp),
        stratify=temp_stratify,
        random_state=random_seed
    )
    
    # 4. Rigorous Data Leakage Verification
    train_hashes = set(train_df["sha256"])
    val_hashes = set(val_df["sha256"])
    test_hashes = set(test_df["sha256"])
    
    train_val_leak = train_hashes.intersection(val_hashes)
    train_test_leak = train_hashes.intersection(test_hashes)
    val_test_leak = val_hashes.intersection(test_hashes)
    
    assert len(train_val_leak) == 0, f"DATA LEAKAGE DETECTED between Train and Val: {len(train_val_leak)} hashes"
    assert len(train_test_leak) == 0, f"DATA LEAKAGE DETECTED between Train and Test: {len(train_test_leak)} hashes"
    assert len(val_test_leak) == 0, f"DATA LEAKAGE DETECTED between Val and Test: {len(val_test_leak)} hashes"
    print("\n[VERIFIED] Zero data leakage: Train, Val, and Test splits share 0 identical content hashes.")
    
    # 5. Calculate Balanced Class Weights
    unique_classes = np.sort(train_df["canonical_category"].unique())
    class_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=unique_classes,
        y=train_df["canonical_category"]
    )
    class_weights = {cls: round(float(w), 4) for cls, w in zip(unique_classes, class_weights_arr)}
    print("\nComputed Balanced Class Weights (for loss rebalancing):")
    for cls, weight in class_weights.items():
        print(f"  {cls:<18}: {weight}")
        
    # 6. Save Split Manifests
    train_out = PROCESSED_DIR / "train_split.csv"
    val_out = PROCESSED_DIR / "val_split.csv"
    test_out = PROCESSED_DIR / "test_split.csv"
    weights_out = PROCESSED_DIR / "class_weights.json"
    config_out = PROCESSED_DIR / "preprocessing_config.json"
    
    train_df.to_csv(train_out, index=False)
    val_df.to_csv(val_out, index=False)
    test_df.to_csv(test_out, index=False)
    
    with open(weights_out, "w", encoding="utf-8") as f:
        json.dump(class_weights, f, indent=2)
        
    preprocessing_config = {
        "image_size": [224, 224],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        },
        "augmentation": {
            "random_horizontal_flip_prob": 0.5,
            "random_rotation_degrees": 15,
            "color_jitter": {"brightness": 0.15, "contrast": 0.15, "saturation": 0.15},
            "random_affine_degrees": 10
        },
        "split_summary": {
            "total_clean_samples": len(clean_df),
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "seed": random_seed
        }
    }
    with open(config_out, "w", encoding="utf-8") as f:
        json.dump(preprocessing_config, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"Splits saved successfully:")
    print(f"  Train: {train_out} ({len(train_df)} samples)")
    print(f"  Val  : {val_out} ({len(val_df)} samples)")
    print(f"  Test : {test_out} ({len(test_df)} samples)")
    print(f"  Weights: {weights_out}")
    print(f"  Config : {config_out}")
    print("=" * 60)
    
    return train_df, val_df, test_df, class_weights

if __name__ == "__main__":
    generate_splits()

