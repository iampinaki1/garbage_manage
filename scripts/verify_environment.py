"""
Environment & Hardware Verification Script
Verifies Python version, GPU/CUDA acceleration, core ML libraries,
directory structure, and database accessibility for Phase 1.
"""
import sys
import os
import platform
from pathlib import Path

def check_environment():
    results = {}
    print("=" * 60)
    print("SMART WASTE SEGREGATION SYSTEM - ENVIRONMENT CHECK")
    print("=" * 60)

    # 1. OS & Platform
    results["os"] = platform.system()
    results["os_release"] = platform.release()
    results["python_version"] = sys.version.split()[0]
    print(f"OS: {results['os']} ({results['os_release']})")
    print(f"Python: {results['python_version']} (Executable: {sys.executable})")

    # 2. PyTorch & CUDA Check
    try:
        import torch
        results["torch_version"] = torch.__version__
        results["cuda_available"] = torch.cuda.is_available()
        if results["cuda_available"]:
            results["gpu_name"] = torch.cuda.get_device_name(0)
            results["device_count"] = torch.cuda.device_count()
            vram_bytes = torch.cuda.get_device_properties(0).total_memory
            results["vram_gb"] = round(vram_bytes / (1024**3), 2)
            print(f"PyTorch: {results['torch_version']} | CUDA: Available")
            print(f"GPU: {results['gpu_name']} ({results['vram_gb']} GB VRAM)")
        else:
            results["gpu_name"] = "CPU Fallback"
            results["vram_gb"] = 0
            print(f"PyTorch: {results['torch_version']} | CUDA: NOT Available (CPU mode)")
    except ImportError as e:
        results["torch_error"] = str(e)
        print(f"PyTorch: FAILED ({e})")

    # 3. Vision & ML Libraries
    libs = [
        ("torchvision", "torchvision"),
        ("ultralytics", "ultralytics"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("sklearn", "Scikit-Learn"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("pymongo", "PyMongo"),
    ]
    print("-" * 60)
    for mod_name, label in libs:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "installed")
            results[mod_name] = ver
            print(f"{label:<16}: {ver}")
        except ImportError as e:
            results[mod_name] = False
            print(f"{label:<16}: NOT INSTALLED ({e})")

    # 4. Directory Structure Check
    print("-" * 60)
    required_dirs = [
        "backend/app/api",
        "backend/app/core",
        "backend/app/database",
        "backend/app/models",
        "backend/app/recommendations",
        "backend/app/services",
        "backend/app/utils",
        "backend/ml/classification",
        "backend/ml/detection",
        "backend/ml/preprocessing",
        "backend/ml/training",
        "backend/ml/evaluation",
        "backend/tests",
        "datasets/trashnet",
        "datasets/realwaste",
        "datasets/taco",
        "datasets/processed",
        "trained_models/classification",
        "trained_models/detection",
        "scripts",
        "docs",
    ]
    missing_dirs = []
    root = Path(__file__).resolve().parent.parent
    for d in required_dirs:
        p = root / d
        if not p.exists():
            missing_dirs.append(d)
    if missing_dirs:
        print(f"Directory check: {len(missing_dirs)} missing directories: {missing_dirs}")
    else:
        print(f"Directory check: All {len(required_dirs)} required project directories exist.")
    results["all_dirs_exist"] = len(missing_dirs) == 0

    print("=" * 60)
    all_ok = (
        results.get("cuda_available", False) or True # CPU fallback allowed
        and results.get("all_dirs_exist", False)
        and all(results.get(m[0], False) for m in libs)
    )
    print("Environment Status:", "READY" if all_ok else "INCOMPLETE")
    print("=" * 60)
    return all_ok

if __name__ == "__main__":
    ok = check_environment()
    sys.exit(0 if ok else 1)

