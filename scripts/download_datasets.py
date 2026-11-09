"""
Dataset Acquisition & Management Script
Downloads, extracts, and validates:
  1. TrashNet: https://github.com/garythung/trashnet
  2. RealWaste: https://archive.ics.uci.edu/dataset/908/realwaste
  3. TACO: https://github.com/pedropro/TACO

Usage:
  python scripts/download_datasets.py --check
  python scripts/download_datasets.py --dataset trashnet
  python scripts/download_datasets.py --dataset taco --max-images 200
  python scripts/download_datasets.py --dataset realwaste
  python scripts/download_datasets.py --all
"""

import os
import sys
import json
import zipfile
import argparse
import urllib.request
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = ROOT / "datasets"
TRASHNET_DIR = DATASETS_DIR / "trashnet"
REALWASTE_DIR = DATASETS_DIR / "realwaste"
TACO_DIR = DATASETS_DIR / "taco"

TRASHNET_URL = "https://raw.githubusercontent.com/garythung/trashnet/master/data/dataset-resized.zip"
REALWASTE_UCI_URL = "https://archive.ics.uci.edu/static/public/908/realwaste.zip"
TACO_ANNOTATIONS_URL = "https://raw.githubusercontent.com/pedropro/TACO/master/data/annotations.json"

def download_file_with_progress(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading from: {url}")
    print(f"Destination: {dest_path}")
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=60) as response:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024 # 1MB
        
        with open(dest_path, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    mb_down = downloaded / (1024 * 1024)
                    mb_tot = total_size / (1024 * 1024)
                    print(f"\r  Progress: {mb_down:.1f}/{mb_tot:.1f} MB ({percent:.1f}%)", end="", flush=True)
                else:
                    mb_down = downloaded / (1024 * 1024)
                    print(f"\r  Downloaded: {mb_down:.1f} MB", end="", flush=True)
        print("\nDownload complete.")

def download_trashnet():
    print("\n--- [1/3] TRASHNET DATASET ---")
    TRASHNET_DIR.mkdir(parents=True, exist_ok=True)
    zip_dest = DATASETS_DIR / "trashnet_raw.zip"
    
    # Check if already extracted
    classes = [d.name for d in TRASHNET_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(classes) >= 6:
        print(f"TrashNet already downloaded & extracted ({len(classes)} classes found: {classes}).")
        return
        
    download_file_with_progress(TRASHNET_URL, zip_dest)
    print(f"Extracting {zip_dest.name} to {TRASHNET_DIR}...")
    with zipfile.ZipFile(zip_dest, "r") as zf:
        zf.extractall(DATASETS_DIR)
        
    # The zip contains a folder called 'dataset-resized'
    nested = DATASETS_DIR / "dataset-resized"
    if nested.exists() and nested.is_dir():
        for item in nested.iterdir():
            target = TRASHNET_DIR / item.name
            if not target.exists():
                item.rename(target)
        try:
            nested.rmdir()
        except Exception:
            pass
            
    if zip_dest.exists():
        zip_dest.unlink() # Cleanup archive
        
    classes = [d.name for d in TRASHNET_DIR.iterdir() if d.is_dir()]
    img_count = sum(len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) for d in TRASHNET_DIR.iterdir() if d.is_dir())
    print(f"TrashNet successfully set up! Classes ({len(classes)}): {classes} | Total images: {img_count}")

def download_taco(max_images: int = 300):
    print("\n--- [2/3] TACO DATASET ---")
    TACO_DIR.mkdir(parents=True, exist_ok=True)
    ann_path = TACO_DIR / "annotations.json"
    
    # 1. Fetch Annotations
    if not ann_path.exists():
        download_file_with_progress(TACO_ANNOTATIONS_URL, ann_path)
    else:
        print(f"Found existing annotations at {ann_path}")
        
    with open(ann_path, "r", encoding="utf-8") as f:
        taco_data = json.load(f)
        
    images = taco_data.get("images", [])
    categories = taco_data.get("categories", [])
    annotations = taco_data.get("annotations", [])
    print(f"TACO metadata: {len(images)} images, {len(categories)} categories, {len(annotations)} annotations")
    
    # 2. Download subset or all images from Flickr URLs
    img_dir = TACO_DIR / "data"
    img_dir.mkdir(parents=True, exist_ok=True)
    
    download_limit = min(max_images, len(images)) if max_images > 0 else len(images)
    print(f"Ensuring {download_limit} TACO images are downloaded into {img_dir}...")
    
    success_count = 0
    fail_count = 0
    for idx, img_info in enumerate(images[:download_limit]):
        file_name = img_info.get("file_name") # e.g. "batch_1/000001.jpg"
        target_path = TACO_DIR / file_name
        if target_path.exists():
            success_count += 1
            continue
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        flickr_url = img_info.get("flickr_url")
        if not flickr_url:
            continue
            
        try:
            req = urllib.request.Request(flickr_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                with open(target_path, "wb") as f_out:
                    f_out.write(r.read())
            success_count += 1
            if (idx + 1) % 25 == 0 or idx + 1 == download_limit:
                print(f"  Downloaded {idx + 1}/{download_limit} TACO images...")
        except Exception as e:
            fail_count += 1
            
    print(f"TACO image status: {success_count} available, {fail_count} failed out of requested {download_limit}.")

def download_realwaste():
    print("\n--- [3/3] REALWASTE DATASET ---")
    REALWASTE_DIR.mkdir(parents=True, exist_ok=True)
    classes = [d.name for d in REALWASTE_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(classes) >= 9:
        print(f"RealWaste already present ({len(classes)} classes found: {classes}).")
        return
        
    zip_dest = DATASETS_DIR / "realwaste_uci.zip"
    try:
        download_file_with_progress(REALWASTE_UCI_URL, zip_dest)
        print(f"Extracting {zip_dest.name} to {REALWASTE_DIR}...")
        with zipfile.ZipFile(zip_dest, "r") as zf:
            zf.extractall(REALWASTE_DIR)
            
        # Check if extracted inside a nested 'realwaste' folder
        nested = REALWASTE_DIR / "realwaste"
        if nested.exists() and nested.is_dir():
            for item in nested.iterdir():
                target = REALWASTE_DIR / item.name
                if not target.exists():
                    item.rename(target)
            try:
                nested.rmdir()
            except Exception:
                pass
                
        if zip_dest.exists():
            zip_dest.unlink()
            
        classes = [d.name for d in REALWASTE_DIR.iterdir() if d.is_dir()]
        img_count = sum(len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) for d in REALWASTE_DIR.iterdir() if d.is_dir())
        print(f"RealWaste successfully set up! Classes ({len(classes)}): {classes} | Total images: {img_count}")
    except Exception as e:
        print(f"Note on RealWaste download: {e}")
        print("RealWaste can also be placed manually in datasets/realwaste/ with subfolders for each category:")
        print("  Cardboard, Food Organics, Glass, Metal, Miscellaneous Trash, Paper, Plastic, Textile Trash, Vegetation")

def check_datasets() -> Dict[str, Any]:
    print("=" * 60)
    print("CURRENT DATASET INVENTORY")
    print("=" * 60)
    status = {}
    
    # TrashNet
    tn_classes = [d.name for d in TRASHNET_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")] if TRASHNET_DIR.exists() else []
    tn_images = sum(len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) for d in TRASHNET_DIR.iterdir() if d.is_dir()) if TRASHNET_DIR.exists() else 0
    status["trashnet"] = {"classes": tn_classes, "image_count": tn_images, "ready": tn_images > 0}
    print(f"TrashNet : {tn_images} images across {len(tn_classes)} classes {tn_classes}")
    
    # RealWaste
    rw_classes = [d.name for d in REALWASTE_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")] if REALWASTE_DIR.exists() else []
    rw_images = sum(len(list(d.glob("*.jpg")) + list(d.glob("*.png"))) for d in REALWASTE_DIR.iterdir() if d.is_dir()) if REALWASTE_DIR.exists() else 0
    status["realwaste"] = {"classes": rw_classes, "image_count": rw_images, "ready": rw_images > 0}
    print(f"RealWaste: {rw_images} images across {len(rw_classes)} classes {rw_classes}")
    
    # TACO
    taco_ann = TACO_DIR / "annotations.json"
    taco_has_ann = taco_ann.exists()
    taco_images = len(list(TACO_DIR.rglob("*.jpg"))) + len(list(TACO_DIR.rglob("*.png"))) if TACO_DIR.exists() else 0
    status["taco"] = {"has_annotations": taco_has_ann, "image_count": taco_images, "ready": taco_has_ann and taco_images > 0}
    print(f"TACO     : Annotations found: {taco_has_ann} | Downloaded images: {taco_images}")
    print("=" * 60)
    return status

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset Acquisition & Verification")
    parser.add_argument("--check", action="store_true", help="Check current datasets status")
    parser.add_argument("--dataset", choices=["trashnet", "realwaste", "taco", "all"], default="check", help="Dataset to download")
    parser.add_argument("--max-images", type=int, default=150, help="Max images for TACO (0 for all 1500)")
    args = parser.parse_args()
    
    if args.check or args.dataset == "check":
        check_datasets()
    elif args.dataset == "trashnet":
        download_trashnet()
        check_datasets()
    elif args.dataset == "realwaste":
        download_realwaste()
        check_datasets()
    elif args.dataset == "taco":
        download_taco(max_images=args.max_images)
        check_datasets()
    elif args.dataset == "all":
        download_trashnet()
        download_taco(max_images=args.max_images)
        download_realwaste()
        check_datasets()

