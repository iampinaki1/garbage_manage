"""
Unified Class Mapping System for Multi-Dataset Waste Segregation.
Reconciles TrashNet, RealWaste, and TACO datasets into 9 standardized categories:
  1. organic_waste
  2. paper_waste
  3. plastic_waste
  4. metal_waste
  5. glass_waste
  6. electronic_waste
  7. hazardous_waste
  8. textile_waste
  9. residual_waste
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CANONICAL_CATEGORIES = [
    "organic_waste",
    "paper_waste",
    "plastic_waste",
    "metal_waste",
    "glass_waste",
    "electronic_waste",
    "hazardous_waste",
    "textile_waste",
    "residual_waste"
]

CANONICAL_TO_DISPLAY = {
    "organic_waste": "Organic Waste",
    "paper_waste": "Paper Waste",
    "plastic_waste": "Plastic Waste",
    "metal_waste": "Metal Waste",
    "glass_waste": "Glass Waste",
    "electronic_waste": "Electronic Waste",
    "hazardous_waste": "Hazardous Waste",
    "textile_waste": "Textile Waste",
    "residual_waste": "Residual Waste"
}

CLASS_TO_ID = {cat: idx for idx, cat in enumerate(CANONICAL_CATEGORIES)}
ID_TO_CLASS = {idx: cat for idx, cat in enumerate(CANONICAL_CATEGORIES)}

# TrashNet mappings (6 classes)
TRASHNET_MAP = {
    "cardboard": "paper_waste",
    "paper": "paper_waste",
    "glass": "glass_waste",
    "metal": "metal_waste",
    "plastic": "plastic_waste",
    "trash": "residual_waste"
}

# RealWaste mappings (9 classes)
REALWASTE_MAP = {
    "cardboard": "paper_waste",
    "paper": "paper_waste",
    "food organics": "organic_waste",
    "vegetation": "organic_waste",
    "glass": "glass_waste",
    "metal": "metal_waste",
    "plastic": "plastic_waste",
    "textile trash": "textile_waste",
    "textile_trash": "textile_waste",
    "miscellaneous trash": "residual_waste",
    "miscellaneous_trash": "residual_waste"
}

# TACO mappings (60 categories)
TACO_MAP = {
    "aluminium foil": "metal_waste",
    "battery": "hazardous_waste",
    "aluminium blister pack": "metal_waste",
    "carded blister pack": "hazardous_waste",
    "other plastic bottle": "plastic_waste",
    "clear plastic bottle": "plastic_waste",
    "glass bottle": "glass_waste",
    "plastic bottle cap": "plastic_waste",
    "metal bottle cap": "metal_waste",
    "broken glass": "glass_waste",
    "food can": "metal_waste",
    "aerosol": "metal_waste",
    "drink can": "metal_waste",
    "toilet tube": "paper_waste",
    "other carton": "paper_waste",
    "egg carton": "paper_waste",
    "drink carton": "paper_waste",
    "corrugated carton": "paper_waste",
    "meal carton": "paper_waste",
    "pizza box": "paper_waste",
    "paper cup": "paper_waste",
    "disposable plastic cup": "plastic_waste",
    "foam cup": "plastic_waste",
    "glass cup": "glass_waste",
    "other plastic cup": "plastic_waste",
    "food waste": "organic_waste",
    "glass jar": "glass_waste",
    "plastic lid": "plastic_waste",
    "metal lid": "metal_waste",
    "other plastic": "plastic_waste",
    "magazine paper": "paper_waste",
    "tissues": "residual_waste",
    "wrapping paper": "paper_waste",
    "normal paper": "paper_waste",
    "paper bag": "paper_waste",
    "plastified paper bag": "plastic_waste",
    "plastic film": "plastic_waste",
    "six pack rings": "plastic_waste",
    "garbage bag": "plastic_waste",
    "other plastic wrapper": "plastic_waste",
    "single-use carrier bag": "plastic_waste",
    "polypropylene bag": "plastic_waste",
    "crisp packet": "plastic_waste",
    "spread tub": "plastic_waste",
    "tupperware": "plastic_waste",
    "disposable food container": "plastic_waste",
    "foam food container": "plastic_waste",
    "other plastic container": "plastic_waste",
    "plastic glooves": "plastic_waste",
    "plastic utensils": "plastic_waste",
    "pop tab": "metal_waste",
    "rope & strings": "textile_waste",
    "scrap metal": "metal_waste",
    "shoe": "textile_waste",
    "squeezable tube": "plastic_waste",
    "plastic straw": "plastic_waste",
    "paper straw": "paper_waste",
    "styrofoam piece": "plastic_waste",
    "unlabeled litter": "residual_waste",
    "cigarette": "residual_waste"
}

def map_raw_label(raw_label: str, source: str = "auto") -> Tuple[str, int]:
    """
    Maps an arbitrary raw dataset label to the canonical waste category.
    Returns: (canonical_category_str, canonical_category_id)
    """
    cleaned = raw_label.strip().lower()
    canonical = None
    
    if source == "trashnet" or source == "auto":
        canonical = TRASHNET_MAP.get(cleaned)
    if not canonical and (source == "realwaste" or source == "auto"):
        canonical = REALWASTE_MAP.get(cleaned)
    if not canonical and (source == "taco" or source == "auto"):
        canonical = TACO_MAP.get(cleaned)
        
    if not canonical:
        # Fallback keywords
        if any(w in cleaned for w in ["paper", "cardboard", "box", "carton"]):
            canonical = "paper_waste"
        elif any(w in cleaned for w in ["plastic", "pet", "hdpe", "bottle", "poly"]):
            canonical = "plastic_waste"
        elif any(w in cleaned for w in ["metal", "can", "foil", "tin", "aluminium"]):
            canonical = "metal_waste"
        elif any(w in cleaned for w in ["glass"]):
            canonical = "glass_waste"
        elif any(w in cleaned for w in ["food", "organic", "fruit", "vegetable"]):
            canonical = "organic_waste"
        elif any(w in cleaned for w in ["battery", "chemical", "hazard"]):
            canonical = "hazardous_waste"
        elif any(w in cleaned for w in ["wire", "electronic", "cable", "circuit"]):
            canonical = "electronic_waste"
        elif any(w in cleaned for w in ["cloth", "textile", "fabric", "shoe"]):
            canonical = "textile_waste"
        else:
            canonical = "residual_waste"
            
    cat_id = CLASS_TO_ID[canonical]
    return canonical, cat_id

def export_mapping_json(output_path: Optional[Path] = None):
    """Saves the class mapping schema as JSON for model training and frontend consumption."""
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "class_mapping.json"
    
    mapping_payload = {
        "num_classes": len(CANONICAL_CATEGORIES),
        "classes": CANONICAL_CATEGORIES,
        "class_to_id": CLASS_TO_ID,
        "id_to_class": ID_TO_CLASS,
        "display_names": CANONICAL_TO_DISPLAY,
        "datasets": {
            "trashnet": TRASHNET_MAP,
            "realwaste": REALWASTE_MAP,
            "taco": TACO_MAP
        }
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping_payload, f, indent=2)
    return output_path

if __name__ == "__main__":
    out = export_mapping_json()
    print(f"Class mapping exported to {out}")
    print(f"Total canonical classes: {len(CANONICAL_CATEGORIES)}")
    for i, c in enumerate(CANONICAL_CATEGORIES):
        print(f"  {i}: {c} -> {CANONICAL_TO_DISPLAY[c]}")

