from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, HttpUrl
from .utils import ok, bad
from .auth import get_current_user
from .dynamodb_client import get_db_client
from .sns import ProductNotificationService

router = APIRouter(prefix="/products", tags=["Products"])

try:
    db = get_db_client()
    notification_service = ProductNotificationService()
except Exception as e:
    raise RuntimeError(f"Failed to initialize services: {e}")

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(..., min_length=1, max_length=1000, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    sku: str = Field(..., min_length=1, max_length=50, description="Stock Keeping Unit (unique)")
    in_stock: int = Field(..., ge=0, description="Current stock quantity")
    reorder_level: int = Field(..., ge=0, description="Minimum stock level before reorder")
    supplier: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, min_length=1, max_length=1000, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price (must be positive)")
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="Product category")
    sku: Optional[str] = Field(None, min_length=1, max_length=50, description="Stock Keeping Unit")
    in_stock: Optional[int] = Field(None, ge=0, description="Current stock quantity")
    reorder_level: Optional[int] = Field(None, ge=0, description="Minimum stock level")
    supplier: Optional[str] = Field(None, min_length=1, max_length=200, description="Supplier name")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")
    is_active: Optional[bool] = Field(None, description="Whether product is active")

@router.get("/")
def get_all_products(current=Depends(get_current_user)):
    """Get all products"""
    try:
        products = db.get_all_products(limit=100)
        return ok("Products fetched", products)
    except Exception as e:
        return bad(500, "DATABASE_ERROR", "Failed to fetch products", str(e))

@router.post("/", status_code=201)
def create_product(body: ProductCreate, current=Depends(get_current_user)):
    try:
        product_data = body.model_dump(mode="json")
        product_data = jsonable_encoder(product_data)
        
        product = db.create_product(product_data)
        
        # Send SNS notification for new product creation
        try:
            notification_service.notify_product_created(product)
        except Exception as notification_error:
            # Log notification error but don't fail the product creation
            print(f"Warning: Failed to send product creation notification: {notification_error}")
        
        return ok("Product created successfully", product, status_code=201)
        
    except ValueError as e:
        return bad(400, "VALIDATION_ERROR", str(e))
    except Exception as e:
        return bad(500, "DATABASE_ERROR", "Failed to create product", str(e))

@router.get("/{product_id}")
def get_product_by_id(product_id: str, current=Depends(get_current_user)):
    """Get a specific product by ID"""
    try:
        product = db.get_product_by_id(product_id)
        if not product:
            return bad(404, "NOT_FOUND", "Product not found")
        
        return ok("Product found", product)
        
    except Exception as e:
        return bad(500, "DATABASE_ERROR", "Failed to fetch product", str(e))

@router.put("/{product_id}")
def update_product_by_id(product_id: str, body: ProductUpdate, current=Depends(get_current_user)):
    """Update a specific product by ID"""
    try:
        existing_product = db.get_product_by_id(product_id)
        if not existing_product:
            return bad(404, "NOT_FOUND", "Product not found")
        
        update_data = body.model_dump(mode="json", exclude_none=True)
        update_data = jsonable_encoder(update_data)
        
        if not update_data:
            return bad(400, "NO_DATA", "No update data provided")
        
        updated_product = db.update_product(product_id, update_data)
        return ok("Product updated successfully", updated_product)
        
    except ValueError as e:
        return bad(400, "VALIDATION_ERROR", str(e))
    except Exception as e:
        return bad(500, "DATABASE_ERROR", "Failed to update product", str(e))

@router.delete("/{product_id}")
def delete_product_by_id(product_id: str, current=Depends(get_current_user)):
    """Delete a specific product by ID"""
    try:
        existing_product = db.get_product_by_id(product_id)
        if not existing_product:
            return bad(404, "NOT_FOUND", "Product not found")
        
        db.delete_product(product_id)
        return ok("Product deleted successfully", {"deleted_product_id": product_id})
        
    except Exception as e:
        return bad(500, "DATABASE_ERROR", "Failed to delete product", str(e))