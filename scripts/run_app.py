"""
Convenient Development & Production Launch Script for Smart Waste Management System.

Usage:
  python scripts/run_app.py --mode dev     # Starts FastAPI backend (port 8000) + Vite dev server (port 5173)
  python scripts/run_app.py --mode api     # Starts FastAPI backend only (port 8000)
  python scripts/run_app.py --mode prod    # Starts FastAPI serving API, static media, and prebuilt React UI
"""

import sys
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def check_environment():
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = Path(sys.executable)
        
    model_a = ROOT / "trained_models" / "classification" / "waste_classifier.pth"
    model_b = ROOT / "trained_models" / "detection" / "waste_yolo.pt"
    
    print("\n=======================================================")
    print(" Smart Waste Segregation & Recycling System Pre-Flight ")
    print("=======================================================")
    print(f"Project Root       : {ROOT}")
    print(f"Python Executable  : {venv_python}")
    print(f"Model A Classifier : {'[READY]' if model_a.exists() else '[MISSING]'}")
    print(f"Model B Detector   : {'[READY]' if model_b.exists() else '[MISSING]'}")
    print("=======================================================\n")
    return venv_python

def run_api_only(python_exe):
    print("Starting FastAPI Backend Server on http://127.0.0.1:8000...")
    cmd = [
        str(python_exe), "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    subprocess.run(cmd, cwd=str(ROOT))

def run_dev_stack(python_exe):
    print("Starting Dual Development Stack:")
    print("  1. FastAPI Backend Server -> http://127.0.0.1:8000 (API & Docs)")
    print("  2. Vite React Frontend    -> http://127.0.0.1:5173 (SaaS Dashboard)")
    print("\nPress Ctrl+C to terminate both servers.\n")
    
    backend_proc = subprocess.Popen([
        str(python_exe), "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ], cwd=str(ROOT))
    
    frontend_dir = ROOT / "frontend"
    frontend_proc = subprocess.Popen(
        ["cmd.exe", "/c", "pnpm run dev"],
        cwd=str(frontend_dir)
    )
    
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down dev servers...")
        backend_proc.terminate()
        frontend_proc.terminate()

def run_production(python_exe):
    dist_dir = ROOT / "frontend" / "dist"
    if not dist_dir.exists():
        print("Frontend production build not found. Running pnpm run build first...")
        subprocess.run(["cmd.exe", "/c", "pnpm run build"], cwd=str(ROOT / "frontend"), check=True)
        
    print("Starting Unified Production Server on http://127.0.0.1:8000...")
    print("  - API & Docs       : http://127.0.0.1:8000/docs")
    print("  - Interactive UI   : http://127.0.0.1:8000/ui")
    subprocess.run([
        str(python_exe), "-m", "uvicorn",
        "backend.app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ], cwd=str(ROOT))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Smart Waste Segregation System")
    parser.add_argument(
        "--mode",
        choices=["dev", "api", "prod"],
        default="api",
        help="Execution mode: 'dev' (API + Vite), 'api' (Backend only), 'prod' (Unified production server)"
    )
    args = parser.parse_args()
    python_exe = check_environment()
    
    if args.mode == "dev":
        run_dev_stack(python_exe)
    elif args.mode == "prod":
        run_production(python_exe)
    else:
        run_api_only(python_exe)

