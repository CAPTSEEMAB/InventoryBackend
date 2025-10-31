import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional
import boto3
from .utils import ok, bad
from .cognito_auth import get_current_cognito_user

router = APIRouter(prefix="/profiles", tags=["Profiles"])

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
TABLE = "user_profiles"

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None

@router.get("/me")
def get_profile(current=Depends(get_current_cognito_user)):
    try:
        table = dynamodb.Table(TABLE)
        response = table.get_item(Key={"id": current["id"]})
        item = response.get("Item")
        if not item:
            return bad(404, "NOT_FOUND", "Profile not found")
        return ok("Profile", item)
    except Exception as e:
        return bad(500, "DB", str(e))

@router.put("/me")
def update_profile(body: ProfileUpdate, current=Depends(get_current_cognito_user)):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return bad(400, "VALIDATION", "Provide at least one field")
    try:
        table = dynamodb.Table(TABLE)
        update_expr = "SET " + ", ".join(f"{k} = :{k}" for k in updates)
        expr_vals = {f":{k}": v for k, v in updates.items()}
        table.update_item(
            Key={"id": current["id"]},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_vals,
            ReturnValues="ALL_NEW"
        )
        # Fetch updated profile
        response = table.get_item(Key={"id": current["id"]})
        item = response.get("Item")
        return ok("Profile updated", item)
    except Exception as e:
        return bad(500, "DB", str(e))
