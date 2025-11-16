import os
from datetime import datetime, timedelta, date
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, HttpUrl

from .utils import ok, bad, get_current_user
from .dynamodb_client import get_db_client

router = APIRouter(prefix="/products", tags=["Products"])

# ─────────────────────────────────────────────
# DynamoDB configuration
# ─────────────────────────────────────────────
try:
    db = get_db_client()
except Exception as e:
    raise RuntimeError(f"Failed to connect to DynamoDB: {e}")

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
    movements_replace: Optional[List[Movement]] = Field(None, description="Replace all movements")
    movements_append: Optional[List[Movement]] = Field(None, description="Append movements")


class MovementCreate(BaseModel):
    movement_type: Literal["IN", "OUT"]
    quantity: int
    movement_date: Optional[str] = None
    unit_cost: Optional[float] = None
    note: Optional[str] = None
    source: Optional[str] = None


# ─────────────────────────────────────────────
# CRUD Endpoints
# ─────────────────────────────────────────────

@router.get("/")
def list_products(current=Depends(get_current_user)):
    """List all products"""
    try:
        products = db.get_all_products(limit=100)
        return ok("Products fetched", products)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.post("/", status_code=201)
def create_product(body: ProductCreate, current=Depends(get_current_user)):
    """Create a new product"""
    try:
        # Convert Pydantic model to dict
        product_data = body.model_dump(mode="json")
        product_data = jsonable_encoder(product_data)
        
        # Create product in DynamoDB
        product = db.create_product(product_data)
        return ok("Product created", product, status_code=201)
        
    except ValueError as e:
        return bad(400, "VALIDATION_ERROR", str(e))
    except Exception as e:
        return bad(500, "DB", str(e))


@router.get("/{product_id}")
def get_product(product_id: str, days: Optional[int] = None, current=Depends(get_current_user)):
    """Get single product (optionally filter movements by days)"""
    try:
        product = db.get_product_by_id(product_id)
        if not product:
            return bad(404, "NOT_FOUND", "Product not found")

        # Filter movements by days if specified
        if days:
            days = max(1, min(365, int(days)))
            from_date = (date.today() - timedelta(days=days)).isoformat()
            movements = product.get("movements", []) or []
            product["movements"] = [m for m in movements if (m.get("movement_date") or "") >= from_date]

        return ok("Product fetched", product)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.put("/{product_id}")
def update_product(product_id: str, body: ProductUpdate, current=Depends(get_current_user)):
    """
    Update only the fields provided in the request body.
    Does not overwrite missing or null fields unless explicitly given.
    """
    try:
        # Check if product exists
        existing = db.get_product_by_id(product_id)
        if not existing:
            return bad(404, "NOT_FOUND", "Product not found")

        # Collect only provided (non-null) fields
        partial = body.model_dump(exclude_unset=True, mode="json")
        updates = {k: v for k, v in partial.items() if v is not None}

        # Handle movements - append or replace
        if body.movements_replace is not None:
            updates["movements"] = body.movements_replace
        elif body.movements_append:
            current_movements = existing.get("movements", []) or []
            updates["movements"] = current_movements + body.movements_append

        # Remove movement control fields from updates
        updates.pop("movements_replace", None)
        updates.pop("movements_append", None)

        # Check if there are any updates
        if not updates:
            return bad(400, "NO_FIELDS", "No valid fields provided to update")

        # Ensure JSON serializable
        updates = jsonable_encoder(updates)

        # Update product in DynamoDB
        updated_product = db.update_product(product_id, updates)
        if not updated_product:
            return bad(500, "DB", "Failed to update product")

        return ok("Product updated", updated_product)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.delete("/{product_id}")
def delete_product(product_id: str, current=Depends(get_current_user)):
    """Delete a product"""
    try:
        success = db.delete_product(product_id)
        if success:
            return ok("Product deleted", None)
        else:
            return bad(404, "NOT_FOUND", "Product not found")
    except Exception as e:
        return bad(500, "DB", str(e))


@router.get("/by-category/{category}")
def get_products_by_category(category: str, current=Depends(get_current_user)):
    """Get products by category"""
    try:
        products = db.get_products_by_category(category)
        return ok(f"Products in category '{category}' fetched", products)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.get("/by-sku/{sku}")
def get_product_by_sku(sku: str, current=Depends(get_current_user)):
    """Get product by SKU"""
    try:
        product = db.get_product_by_sku(sku)
        if not product:
            return bad(404, "NOT_FOUND", "Product with this SKU not found")
        return ok("Product fetched by SKU", product)
    except Exception as e:
        return bad(500, "DB", str(e))


@router.post("/{product_id}/movements")
def add_stock_movement(
    product_id: str, 
    body: MovementCreate,
    current=Depends(get_current_user)
):
    """Add stock movement to product"""
    try:
        success = db.add_stock_movement(
            product_id, 
            body.movement_type, 
            body.quantity, 
            body.movement_date
        )
        if success:
            # Get updated product to return
            product = db.get_product_by_id(product_id)
            return ok("Stock movement added", product)
        else:
            return bad(404, "NOT_FOUND", "Product not found")
    except Exception as e:
        return bad(500, "DB", str(e))