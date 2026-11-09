"""
Dataset Inspection & Integrity Verification Module.
Requirements handled:
  1. Inspect dataset directory structures.
  2. Identify available classes and read existing annotations.
  3. Detect corrupted, truncated, and duplicate images.
  4. Generate detailed dataset statistics and class imbalance ratios.
  5. Compute image dimension distributions (min, max, mean, aspect ratios).
  6. Export structured JSON & Markdown reports for audit compliance.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
from PIL import Image
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.preprocessing.class_mapping import map_raw_label, CANONICAL_CATEGORIES

DATASETS_DIR = ROOT / "datasets"
PROCESSED_DIR = ROOT / "datasets" / "processed"
DOCS_DIR = ROOT / "docs"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def compute_file_hash(path: Path) -> str:
    """Computes SHA-256 hash of file content to detect exact bit-level duplicates."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def inspect_image(path: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Attempts to read and verify image integrity using Pillow.
    Returns: (is_valid, error_msg, metadata)
    """
    try:
        with Image.open(path) as img:
            img.verify() # Checks header and structural integrity
        # Re-open to read dimensions and mode (verify closes file stream)
        with Image.open(path) as img:
            width, height = img.size
            mode = img.mode
            channels = len(img.getbands())
            aspect_ratio = round(width / max(1, height), 4)
            file_size_kb = round(path.stat().st_size / 1024, 2)
            
            # Check for zero or degenerate dimensions
            if width <= 0 or height <= 0:
                return False, "Degenerate dimensions (width or height <= 0)", {}
                
            return True, "", {
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "mode": mode,
                "channels": channels,
                "file_size_kb": file_size_kb
            }
    except Exception as e:
        return False, str(e), {}

def run_inspection(sample_limit: int = 0) -> Dict[str, Any]:
    print("=" * 60)
    print("RUNNING COMPREHENSIVE DATASET INSPECTION & INTEGRITY CHECK")
    print("=" * 60)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    records = []
    seen_hashes = {} # hash -> first seen path
    corrupt_files = []
    duplicates = []
    
    datasets_to_scan = [
        ("trashnet", DATASETS_DIR / "trashnet"),
        ("realwaste", DATASETS_DIR / "realwaste"),
        ("taco", DATASETS_DIR / "taco")
    ]
    
    # 1. Read TACO annotations if available to cross-reference bounding boxes
    taco_ann_map = {}
    taco_ann_path = DATASETS_DIR / "taco" / "annotations.json"
    if taco_ann_path.exists():
        try:
            with open(taco_ann_path, "r", encoding="utf-8") as f:
                taco_json = json.load(f)
                cat_id_to_name = {c["id"]: c["name"] for c in taco_json.get("categories", [])}
                img_id_to_name = {im["id"]: im["file_name"] for im in taco_json.get("images", [])}
                for ann in taco_json.get("annotations", []):
                    img_name = img_id_to_name.get(ann["image_id"])
                    cat_name = cat_id_to_name.get(ann["category_id"])
                    if img_name:
                        taco_ann_map.setdefault(img_name, []).append({
                            "category": cat_name,
                            "bbox": ann.get("bbox")
                        })
        except Exception as e:
            print(f"Warning: Could not parse TACO annotations.json: {e}")
            
    # 2. Traverse datasets
    total_scanned = 0
    for dataset_name, dir_path in datasets_to_scan:
        if not dir_path.exists():
            continue
            
        print(f"Scanning {dataset_name} at: {dir_path}")
        image_files = [p for p in dir_path.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        
        for img_path in image_files:
            total_scanned += 1
            if sample_limit > 0 and total_scanned > sample_limit:
                break
                
            # Determine raw label
            if dataset_name == "trashnet":
                raw_label = img_path.parent.name
            elif dataset_name == "realwaste":
                raw_label = img_path.parent.name
            elif dataset_name == "taco":
                rel = str(img_path.relative_to(dir_path)).replace("\\", "/")
                anns = taco_ann_map.get(rel, [])
                raw_label = anns[0]["category"] if anns else "unlabeled litter"
            else:
                raw_label = "unknown"
                
            canonical_cat, cat_id = map_raw_label(raw_label, source=dataset_name)
            
            # Verify image integrity
            is_valid, err_msg, meta = inspect_image(img_path)
            if not is_valid:
                corrupt_files.append({"path": str(img_path), "error": err_msg, "dataset": dataset_name})
                continue
                
            # Content Hash & Duplicate Detection
            file_hash = compute_file_hash(img_path)
            is_duplicate = file_hash in seen_hashes
            if is_duplicate:
                duplicates.append({
                    "original": str(seen_hashes[file_hash]),
                    "duplicate": str(img_path),
                    "hash": file_hash
                })
            else:
                seen_hashes[file_hash] = img_path
                
            records.append({
                "file_path": str(img_path.resolve()),
                "relative_path": str(img_path.relative_to(ROOT)),
                "dataset": dataset_name,
                "raw_label": raw_label,
                "canonical_category": canonical_cat,
                "category_id": cat_id,
                "width": meta["width"],
                "height": meta["height"],
                "aspect_ratio": meta["aspect_ratio"],
                "channels": meta["channels"],
                "file_size_kb": meta["file_size_kb"],
                "sha256": file_hash,
                "is_duplicate": is_duplicate,
                "is_valid": True
            })
            
    df = pd.DataFrame(records)
    print(f"\nScan Complete: {total_scanned} files inspected | {len(df)} valid records | {len(corrupt_files)} corrupt | {len(duplicates)} duplicates")
    
    # 3. Statistics Calculation
    valid_unique_df = df[~df["is_duplicate"]] if not df.empty else df
    
    canonical_counts = valid_unique_df["canonical_category"].value_counts().to_dict() if not valid_unique_df.empty else {}
    for c in CANONICAL_CATEGORIES:
        canonical_counts.setdefault(c, 0)
        
    counts_list = [v for v in canonical_counts.values() if v > 0]
    imbalance_ratio = round(max(counts_list) / max(1, min(counts_list)), 2) if counts_list else 1.0
    
    dim_stats = {}
    if not valid_unique_df.empty:
        dim_stats = {
            "min_width": int(valid_unique_df["width"].min()),
            "max_width": int(valid_unique_df["width"].max()),
            "mean_width": round(float(valid_unique_df["width"].mean()), 1),
            "min_height": int(valid_unique_df["height"].min()),
            "max_height": int(valid_unique_df["height"].max()),
            "mean_height": round(float(valid_unique_df["height"].mean()), 1),
            "mean_aspect_ratio": round(float(valid_unique_df["aspect_ratio"].mean()), 2)
        }
        
    report = {
        "summary": {
            "total_images_scanned": total_scanned,
            "valid_images": len(df),
            "unique_valid_images": len(valid_unique_df),
            "corrupted_images_count": len(corrupt_files),
            "duplicate_images_count": len(duplicates),
            "imbalance_ratio": imbalance_ratio
        },
        "datasets_breakdown": df["dataset"].value_counts().to_dict() if not df.empty else {},
        "canonical_distribution": canonical_counts,
        "dimension_statistics": dim_stats,
        "corrupted_files": corrupt_files[:20],
        "duplicate_files": duplicates[:20]
    }
    
    # 4. Save metadata CSV and JSON report
    csv_out = PROCESSED_DIR / "dataset_metadata.csv"
    json_out = PROCESSED_DIR / "dataset_report.json"
    df.to_csv(csv_out, index=False)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    # 5. Generate Markdown Report
    generate_markdown_report(report, DOCS_DIR / "dataset_inspection_report.md")
    
    print(f"Metadata exported: {csv_out}")
    print(f"JSON Report exported: {json_out}")
    print(f"Markdown Report exported: {DOCS_DIR / 'dataset_inspection_report.md'}")
    return report

def generate_markdown_report(report: Dict[str, Any], output_path: Path):
    s = report["summary"]
    dims = report.get("dimension_statistics", {})
    
    md = f"""# Dataset Inspection, Integrity & Statistical Analysis Report

## 1. Overview & Integrity Verification
- **Total Images Scanned**: {s['total_images_scanned']}
- **Valid & Structurally Intact Images**: {s['valid_images']}
- **Unique Clean Images**: {s['unique_valid_images']}
- **Corrupted / Truncated Images Detected**: {s['corrupted_images_count']}
- **Duplicate Images Detected (SHA-256)**: {s['duplicate_images_count']}
- **Class Imbalance Ratio (Max / Min non-zero)**: {s['imbalance_ratio']}x

---

## 2. Dataset Distribution by Source
| Dataset Source | Image Count | Status |
| :--- | :--- | :--- |
"""
    for ds, count in report.get("datasets_breakdown", {}).items():
        md += f"| **{ds.capitalize()}** | {count} | Verified |\n"
        
    md += f"""
---

## 3. Canonical Waste Category Distribution
| Category ID | Canonical Category | Sample Count | Percentage |
| :--- | :--- | :--- | :--- |
"""
    total_unique = max(1, s["unique_valid_images"])
    for idx, cat in enumerate(CANONICAL_CATEGORIES):
        count = report["canonical_distribution"].get(cat, 0)
        pct = round((count / total_unique) * 100, 2)
        md += f"| {idx} | `{cat}` | {count} | {pct}% |\n"

    md += f"""
---

## 4. Image Dimensional Statistics
- **Resolution Range**: {dims.get('min_width', 0)}x{dims.get('min_height', 0)} to {dims.get('max_width', 0)}x{dims.get('max_height', 0)} px
- **Average Resolution**: {dims.get('mean_width', 0)} x {dims.get('mean_height', 0)} px
- **Mean Aspect Ratio (W/H)**: {dims.get('mean_aspect_ratio', 0)}

---

## 5. Preprocessing & Mitigation Strategy
1. **Duplicate Exclusion**: All detected duplicate content hashes are quarantined to avoid identical images appearing in both train and test splits (preventing data leakage).
2. **Class Imbalance Handling**: Class weights are computed via `compute_class_weight('balanced')` to apply loss weighting during model training, supplemented by targeted data augmentation for under-represented categories.
3. **Dimension Normalization**: All classification images are resized and standardized to `224x224` with ImageNet normalization tensors, while YOLO detection images are scaled to `640x640`.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    run_inspection()

