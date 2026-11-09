"""
Authentication and User Identity Endpoints.
"""

from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from backend.app.core.config import settings
from backend.app.database.connection import db_manager
from backend.app.models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfile
)
from backend.app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: UserRegisterRequest):
    """Registers a new user and returns JWT access credentials."""
    users_col = db_manager.get_collection("users")
    
    # Check if username or email already exists
    existing_user = await users_col.find_one({"$or": [{"username": request.username}, {"email": request.email}]})
    # If using in-memory collection without $or query, handle explicit query:
    if not existing_user:
        existing_by_user = await users_col.find_one({"username": request.username})
        existing_by_email = await users_col.find_one({"email": request.email})
        existing_user = existing_by_user or existing_by_email

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered."
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(request.password)
    now_iso = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "_id": user_id,
        "username": request.username,
        "email": request.email,
        "full_name": request.full_name or request.username,
        "hashed_password": hashed_pwd,
        "role": "user",
        "created_at": now_iso
    }
    
    await users_col.insert_one(user_doc)
    
    # Generate token
    token = create_access_token({"sub": request.username, "user_id": user_id})
    profile = UserProfile(
        id=user_id,
        username=request.username,
        email=request.email,
        full_name=user_doc["full_name"],
        role="user",
        created_at=now_iso
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=profile
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(request: UserLoginRequest):
    """Authenticates user credentials and issues JWT token."""
    users_col = db_manager.get_collection("users")
    
    user = await users_col.find_one({"username": request.username_or_email})
    if not user:
        user = await users_col.find_one({"email": request.username_or_email})
        
    if not user or not verify_password(request.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user["username"], "user_id": str(user["_id"])})
    profile = UserProfile(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        role=user.get("role", "user"),
        created_at=user.get("created_at", datetime.now(timezone.utc).isoformat())
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=profile
    )


@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: UserProfile = Depends(get_current_user)):
    """Returns currently authenticated user profile."""
    return current_user

