"""
COCO to YOLO Format Annotation Converter.
Converts TACO COCO-formatted annotations into standard Ultralytics YOLO format:
  - Input: COCO annotations.json with bounding boxes [x_min, y_min, width, height]
  - Output: YOLO text labels with [class_id, x_center, y_center, width, height] normalized to [0.0, 1.0]
  - Generates data.yaml configuration file for Ultralytics YOLO training.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.ml.preprocessing.class_mapping import map_raw_label, CANONICAL_CATEGORIES, CLASS_TO_ID

DATASETS_DIR = ROOT / "datasets"
TACO_DIR = DATASETS_DIR / "taco"
YOLO_OUTPUT_DIR = DATASETS_DIR / "processed" / "yolo"

def coco_to_yolo_bbox(
    coco_bbox: List[float],
    img_width: int,
    img_height: int
) -> Tuple[float, float, float, float]:
    """
    Converts COCO [x_min, y_min, width, height] in pixels
    to YOLO [x_center, y_center, width, height] normalized to [0, 1].
    """
    x_min, y_min, box_w, box_h = coco_bbox
    
    # Calculate center point
    x_center = x_min + (box_w / 2.0)
    y_center = y_min + (box_h / 2.0)
    
    # Normalize by image dimensions
    norm_x = x_center / img_width
    norm_y = y_center / img_height
    norm_w = box_w / img_width
    norm_h = box_h / img_height
    
    # Clip to [0.0, 1.0] boundary
    norm_x = max(0.0, min(1.0, norm_x))
    norm_y = max(0.0, min(1.0, norm_y))
    norm_w = max(0.0, min(1.0, norm_w))
    norm_h = max(0.0, min(1.0, norm_h))
    
    return round(norm_x, 6), round(norm_y, 6), round(norm_w, 6), round(norm_h, 6)

def convert_taco_to_yolo(
    val_ratio: float = 0.2,
    random_seed: int = 42
) -> Dict[str, Any]:
    print("=" * 60)
    print("CONVERTING TACO COCO ANNOTATIONS TO ULTRALYTICS YOLO FORMAT")
    print("=" * 60)
    
    ann_file = TACO_DIR / "annotations.json"
    if not ann_file.exists():
        raise FileNotFoundError(f"TACO annotations file not found at: {ann_file}")
        
    with open(ann_file, "r", encoding="utf-8") as f:
        coco_data = json.load(f)
        
    categories = {c["id"]: c["name"] for c in coco_data.get("categories", [])}
    images_meta = {im["id"]: im for im in coco_data.get("images", [])}
    
    # Group annotations by image_id
    img_annotations: Dict[int, List[Dict[str, Any]]] = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann["image_id"]
        img_annotations.setdefault(img_id, []).append(ann)
        
    print(f"Loaded {len(categories)} TACO categories, {len(images_meta)} image metadata entries, {len(coco_data.get('annotations', []))} annotations.")
    
    # Setup YOLO directory structure
    for split in ["train", "val"]:
        (YOLO_OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (YOLO_OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)
        
    # Find existing local TACO image files
    converted_count = 0
    total_boxes = 0
    degenerate_boxes = 0
    
    available_images = []
    for img_id, img_info in images_meta.items():
        rel_path = img_info["file_name"] # e.g. "batch_1/000001.jpg"
        abs_img_path = TACO_DIR / rel_path
        if abs_img_path.exists():
            available_images.append(img_info)
            
    print(f"Found {len(available_images)} locally downloaded TACO image files.")
    
    import random
    random.seed(random_seed)
    random.shuffle(available_images)
    
    val_count = int(len(available_images) * val_ratio)
    val_set = set(im["id"] for im in available_images[:val_count])
    
    for img_info in available_images:
        img_id = img_info["id"]
        rel_path = img_info["file_name"]
        src_path = TACO_DIR / rel_path
        
        split = "val" if img_id in val_set else "train"
        dest_img_path = YOLO_OUTPUT_DIR / "images" / split / f"taco_{img_id:06d}{src_path.suffix}"
        dest_txt_path = YOLO_OUTPUT_DIR / "labels" / split / f"taco_{img_id:06d}.txt"
        
        # Copy image file
        shutil.copy2(src_path, dest_img_path)
        
        img_w = img_info["width"]
        img_h = img_info["height"]
        
        anns = img_annotations.get(img_id, [])
        yolo_lines = []
        for ann in anns:
            coco_bbox = ann.get("bbox")
            if not coco_bbox or len(coco_bbox) != 4:
                continue
            if coco_bbox[2] <= 0 or coco_bbox[3] <= 0:
                degenerate_boxes += 1
                continue
                
            raw_cat_name = categories.get(ann["category_id"], "unlabeled litter")
            canonical_cat, cat_id = map_raw_label(raw_cat_name, source="taco")
            
            nx, ny, nw, nh = coco_to_yolo_bbox(coco_bbox, img_w, img_h)
            if nw <= 0.001 or nh <= 0.001:
                degenerate_boxes += 1
                continue
                
            yolo_lines.append(f"{cat_id} {nx:.6f} {ny:.6f} {nw:.6f} {nh:.6f}")
            total_boxes += 1
            
        with open(dest_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(yolo_lines))
            
        converted_count += 1
        
    # Generate data.yaml for Ultralytics YOLO
    yaml_content = {
        "path": str(YOLO_OUTPUT_DIR.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "nc": len(CANONICAL_CATEGORIES),
        "names": {idx: name for idx, name in enumerate(CANONICAL_CATEGORIES)}
    }
    yaml_path = YOLO_OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, sort_keys=False)
        
    print(f"\nConversion Summary:")
    print(f"  Converted Images : {converted_count}")
    print(f"  Total Valid Boxes: {total_boxes}")
    print(f"  Degenerate Boxes Ignored: {degenerate_boxes}")
    print(f"  YAML Config      : {yaml_path}")
    print("=" * 60)
    
    return {
        "converted_images": converted_count,
        "total_boxes": total_boxes,
        "degenerate_boxes": degenerate_boxes,
        "yaml_path": str(yaml_path)
    }

if __name__ == "__main__":
    convert_taco_to_yolo()

