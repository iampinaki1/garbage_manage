"""
Authentication and Authorization service.
Handles cryptographic password hashing, JWT token lifecycle, and user persistence.
"""

import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.core.config import settings
from backend.app.database.connection import db_manager
from backend.app.models.schemas import UserProfile

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Computes PBKDF2-HMAC-SHA256 hash with a cryptographically secure random salt."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against salt:key hash format."""
    try:
        salt, key = hashed_password.split(":")
        check = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), bytes.fromhex(salt), 100000)
        return check.hex() == key
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserProfile:
    """Dependency for strictly protected endpoints."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
        
    users_col = db_manager.get_collection("users")
    user = await users_col.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        
    return UserProfile(
        id=str(user.get("_id", "")),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        role=user.get("role", "user"),
        created_at=user.get("created_at", datetime.now(timezone.utc).isoformat())
    )


async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[UserProfile]:
    """Dependency for endpoints with optional user association (e.g. anonymous analysis)."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except Exception:
        return None

