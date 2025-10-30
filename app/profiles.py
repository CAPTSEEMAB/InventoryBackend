import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional
from supabase import create_client
from .utils import ok, bad, get_current_user

router = APIRouter(prefix="/profiles", tags=["Profiles"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
db = create_client(SUPABASE_URL, SERVICE_ROLE)
TABLE = "user_profiles"

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None

@router.get("/me")
def get_profile(current=Depends(get_current_user)):
    try:
        res = db.table(TABLE).select("*").eq("id", current["id"]).limit(1).execute()
        return ok("Profile", res.data[0] if res.data else None)
    except Exception as e:
        return bad(500, "DB", str(e))

@router.put("/me")
def update_profile(body: ProfileUpdate, current=Depends(get_current_user)):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return bad(400, "VALIDATION", "Provide at least one field")
    try:
        res = db.table(TABLE).update(updates).eq("id", current["id"]).select("*").execute()
        return ok("Profile updated", res.data[0] if res.data else None)
    except Exception as e:
        return bad(500, "DB", str(e))
