"""
Application Configuration Settings.
Loads configuration from environment variables with safe defaults.
"""

import os
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent.parent.parent

class Settings:
    PROJECT_NAME: str = "Smart Waste Segregation and Recycling Recommendation System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security & Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "smart-waste-segregation-secret-key-2026-very-secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "waste_segregation_db")
    
    # Paths & Static Storage
    ROOT_DIR: Path = ROOT
    FRONTEND_DIST: Path = ROOT / "frontend" / "dist"
    STATIC_DIR: Path = ROOT / "backend" / "static"
    ANNOTATED_DIR: Path = ROOT / "backend" / "static" / "annotated"
    UPLOADS_DIR: Path = ROOT / "backend" / "static" / "uploads"
    
    # Model Paths
    CLASSIFIER_WEIGHTS: Path = ROOT / "trained_models" / "classification" / "waste_classifier.pth"
    DETECTOR_WEIGHTS: Path = ROOT / "trained_models" / "detection" / "waste_yolo.pt"
    RECYCLING_CSV: Path = ROOT / "backend" / "recommendations" / "recycling_data.csv"
    
    # Upload Constraints
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024 # 10 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/bmp"]
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()

# Ensure static directories exist
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
settings.ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

