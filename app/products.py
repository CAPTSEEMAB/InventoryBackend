import os
from datetime import datetime, timedelta, date
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, HttpUrl
from supabase import create_client

from .utils import ok, bad, get_current_user

router = APIRouter(prefix="/products", tags=["Products"])

# ─────────────────────────────────────────────
# Supabase configuration
# ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

db = create_client(SUPABASE_URL, SERVICE_ROLE)
TABLE = "inventory_products"

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
                "is_active": True,
                "description": "Stainless steel French press coffee maker with heat-resistant glass and reusable filter."
            }
        }


# ─────────────────────────────────────────────
# CRUD Endpoints
# ─────────────────────────────────────────────

@router.get("/")
def list_products(current=Depends(get_current_user)):
    """List all products"""
    try:
        res = db.table(TABLE).select("*").order("created_at", desc=True).execute()
        return ok("Products fetched", res.data)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.post("/", status_code=201)
def create_product(body: ProductCreate, current=Depends(get_current_user)):
    """Create a new product"""
    try:
        # ✅ Ensure everything is JSON-serializable (HttpUrl, nested lists, etc.)
        insert_data = body.model_dump(mode="json")
        insert_data = jsonable_encoder(insert_data)

        insert_res = db.table(TABLE).insert(insert_data).execute()

        if insert_res.data and len(insert_res.data) > 0:
            product_id = insert_res.data[0]["id"]
            fetch_res = db.table(TABLE).select("*").eq("id", product_id).execute()
            return ok("Product created", fetch_res.data[0] if fetch_res.data else None, status_code=201)

        return bad(500, "DB", "Insert succeeded but no data returned")
    except Exception as e:
        return bad(500, "DB", str(e))


@router.get("/{product_id}")
def get_product(product_id: str, days: Optional[int] = None, current=Depends(get_current_user)):
    """Get single product (optionally filter movements by days)"""
    try:
        res = db.table(TABLE).select("*").eq("id", product_id).execute()
        if not res.data:
            return bad(404, "NOT_FOUND", "Product not found")

        item = res.data[0]
        if days:
            days = max(1, min(365, int(days)))
            from_date = (date.today() - timedelta(days=days)).isoformat()
            movements = item.get("movements", []) or []
            item["movements"] = [m for m in movements if (m.get("movement_date") or "") >= from_date]

        return ok("Product fetched", item)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.put("/{product_id}")
def update_product(product_id: str, body: ProductUpdate, current=Depends(get_current_user)):
    """
    Update only the fields provided in the request body.
    Does not overwrite missing or null fields unless explicitly given.
    """
    try:
        # 1️⃣ Fetch existing record
        existing_res = db.table(TABLE).select("*").eq("id", product_id).execute()
        if not existing_res.data:
            return bad(404, "NOT_FOUND", "Product not found")

        existing = existing_res.data[0]

        # 2️⃣ Collect only provided (non-null) fields, JSON-serializable
        partial = body.model_dump(exclude_unset=True, mode="json")
        updates = {k: v for k, v in partial.items() if v is not None}

        # Movement handling (append/replace) uses plain python lists/dicts (JSON-safe)
        if body.movements_replace is not None:
            updates["movements"] = body.movements_replace
        elif body.movements_append:
            current_movs = existing.get("movements", []) or []
            updates["movements"] = current_movs + body.movements_append

        # updated_at always refreshed
        updates["updated_at"] = datetime.utcnow().isoformat()

        # nothing to change?
        if len(updates) <= 1:  # only has updated_at
            return bad(400, "NO_FIELDS", "No valid fields provided to update")

        # ✅ Final JSON encoding to avoid “not JSON serializable”
        updates = jsonable_encoder(updates)

        # 5️⃣ Perform update
        upd_res = db.table(TABLE).update(updates).eq("id", product_id).execute()

        # 6️⃣ Return updated data
        if upd_res.data:
            return ok("Product updated", upd_res.data[0])

        # fallback fetch
        latest = db.table(TABLE).select("*").eq("id", product_id).execute()
        return ok("Product updated", latest.data[0] if latest.data else None)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.delete("/{product_id}")
def delete_product(product_id: str, current=Depends(get_current_user)):
    """Delete a product"""
    try:
        db.table(TABLE).delete().eq("id", product_id).execute()
        return ok("Product deleted", None)
    except Exception as e:
        return bad(500, "DB", str(e))
