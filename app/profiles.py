import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional
from .utils import ok, bad, get_current_user
from .dynamodb_client import get_db_client

router = APIRouter(prefix="/profiles", tags=["Profiles"])

# ─────────────────────────────────────────────
# DynamoDB configuration
# ─────────────────────────────────────────────
try:
    db = get_db_client()
except Exception as e:
    raise RuntimeError(f"Failed to connect to DynamoDB: {e}")

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

@router.get("/me")
def get_profile(current=Depends(get_current_user)):
    """Get current user's profile"""
    try:
        profile = db.get_user_by_id(current["id"])
        if not profile:
            return bad(404, "NOT_FOUND", "Profile not found")
        
        # Remove sensitive information
        safe_profile = {k: v for k, v in profile.items() if k != "password_hash"}
        return ok("Profile fetched", safe_profile)
    except Exception as e:
        return bad(500, "DB", str(e))

@router.put("/me")
def update_profile(body: ProfileUpdate, current=Depends(get_current_user)):
    """Update current user's profile"""
    try:
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return bad(400, "VALIDATION", "Provide at least one field to update")
        
        updated_profile = db.update_user_profile(current["id"], updates)
        if not updated_profile:
            return bad(404, "NOT_FOUND", "Profile not found")
        
        # Remove sensitive information
        safe_profile = {k: v for k, v in updated_profile.items() if k != "password_hash"}
        return ok("Profile updated", safe_profile)
    except Exception as e:
        return bad(500, "DB", str(e))

@router.delete("/me")
def delete_profile(current=Depends(get_current_user)):
    """Delete current user's profile"""
    try:
        success = db.delete_user_profile(current["id"])
        if success:
            return ok("Profile deleted", None)
        else:
            return bad(404, "NOT_FOUND", "Profile not found")
    except Exception as e:
        return bad(500, "DB", str(e))