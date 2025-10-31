import os
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, HttpUrl
import boto3

from .utils import ok, bad
from .cognito_auth import get_current_cognito_user

router = APIRouter(prefix="/products", tags=["Products"])

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class Movement(BaseModel):
    movement_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    type: Literal["IN", "OUT"]
    quantity: int
    unit_cost: Optional[float] = None
    note: Optional[str] = None
    source: Optional[str] = None
    reference_id: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    price: Optional[float] = None
    reorder_level: Optional[int] = 0
    in_stock: Optional[int] = 0
    image_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = True
    description: Optional[str] = None
    movements: List[Movement] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    price: Optional[float] = None
    reorder_level: Optional[int] = None
    in_stock: Optional[int] = None
    image_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    movements_replace: Optional[List[Movement]] = None
    movements_append: Optional[List[Movement]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "French Press Coffee Maker 1L",
                "category": "Equipment",
                "supplier": "CafeGear Pro",
                "price": 24.99,
                "reorder_level": 5,
                "in_stock": 15,
                "description": "Stainless steel French press coffee maker with heat-resistant glass and reusable filter."
            }
        }

# ─────────────────────────────────────────────
# AWS DynamoDB configuration
# ─────────────────────────────────────────────
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
TABLE = "inventory_products"


# Helpers
def _table():
    return dynamodb.Table(TABLE)


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


# ─────────────────────────────────────────────
# CRUD Endpoints
# ─────────────────────────────────────────────
@router.get("/")
def list_products(current=Depends(get_current_cognito_user)):
    """List all products"""
    try:
        table = _table()
        resp = table.scan()
        items = resp.get("Items", [])
        return ok("Products fetched", items)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.post("/", status_code=201)
def create_product(body: ProductCreate, current=Depends(get_current_cognito_user)):
    """Create a new product"""
    try:
        table = _table()
        item = body.model_dump(mode="json")
        item["id"] = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        item.setdefault("movements", [])
        item["created_at"] = now
        item["updated_at"] = now
        # ensure JSON-serializable
        item = jsonable_encoder(item)
        table.put_item(Item=item)
        return ok("Product created", item, status_code=201)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.get("/{product_id}")
def get_product(product_id: str, days: Optional[int] = None, current=Depends(get_current_cognito_user)):
    """Get single product (optionally filter movements by days)"""
    try:
        table = _table()
        resp = table.get_item(Key={"id": product_id})
        item = resp.get("Item")
        if not item:
            return bad(404, "NOT_FOUND", "Product not found")
        if days is not None:
            cutoff = date.today() - timedelta(days=days)
            movs = item.get("movements", []) or []
            filtered = [
                m for m in movs
                if _parse_date(m.get("movement_date")) >= cutoff
            ]
            item["movements"] = filtered
        return ok("Product fetched", item)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.put("/{product_id}")
def update_product(product_id: str, body: ProductUpdate, current=Depends(get_current_cognito_user)):
    """
    Update only the fields provided in the request body.
    Does not overwrite missing or null fields unless explicitly given.
    """
    try:
        table = _table()
        resp = table.get_item(Key={"id": product_id})
        existing = resp.get("Item")
        if not existing:
            return bad(404, "NOT_FOUND", "Product not found")

        # Collect only provided (non-null) fields, JSON-serializable
        partial = body.model_dump(exclude_unset=True, mode="json")
        updates = {k: v for k, v in partial.items() if v is not None}

        # Movement handling (append/replace)
        if "movements_replace" in updates and updates["movements_replace"] is not None:
            updates["movements"] = updates.pop("movements_replace")
        elif "movements_append" in updates and updates["movements_append"]:
            current_movs = existing.get("movements", []) or []
            append_list = updates.pop("movements_append")
            updates["movements"] = current_movs + append_list

        # updated_at always refreshed
        updates["updated_at"] = datetime.utcnow().isoformat()

        # nothing to change?
        # if updates only contains updated_at and nothing else, reject
        if set(updates.keys()) <= {"updated_at"}:
            return bad(400, "NO_FIELDS", "No valid fields provided to update")

        # Merge updates into existing item and write back
        merged = {**existing, **updates}
        merged = jsonable_encoder(merged)
        table.put_item(Item=merged)
        return ok("Product updated", merged)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.delete("/{product_id}")
def delete_product(product_id: str, current=Depends(get_current_cognito_user)):
    """Delete a product"""
    try:
        table = _table()
        table.delete_item(Key={"id": product_id})
        return ok("Product deleted", None)
    except Exception as e:
        return bad(500, "DB", str(e))
