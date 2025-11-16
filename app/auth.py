import os
import hashlib
from fastapi import APIRouter
from pydantic import BaseModel
from .utils import ok, bad, sign_jwt
from .dynamodb_client import get_db_client

# ─────────────────────────────────────────────
# DynamoDB client setup
# ─────────────────────────────────────────────
try:
    db = get_db_client()
except Exception as e:
    raise RuntimeError(f"Failed to connect to DynamoDB: {e}")

router = APIRouter(prefix="/auth", tags=["Auth"])

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "inventory_api_salt_2024"  # In production, use individual salts
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────
class SignupBody(BaseModel):
    email: str
    password: str
    name: str

class LoginBody(BaseModel):
    email: str
    password: str

# ─────────────────────────────────────────────
# Signup - Create new user with DynamoDB
# ─────────────────────────────────────────────
@router.post("/signup")
def signup(body: SignupBody):
    """
    Create a new user account in DynamoDB
    """
    try:
        # Check if user already exists
        existing_user = db.get_user_by_email(body.email)
        if existing_user:
            return bad(400, "USER_EXISTS", "User with this email already exists")
        
        # Hash password
        password_hash = hash_password(body.password)
        
        # Create user profile
        user = db.create_user_profile(
            email=body.email,
            name=body.name,
            password_hash=password_hash
        )
        
        # Generate JWT token
        token = sign_jwt({
            "id": user["id"],
            "email": user["email"],
            "role": "USER"
        })
        
        return ok("User created successfully", {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"]
            }
        })
        
    except ValueError as e:
        return bad(400, "SIGNUP_FAILED", str(e))
    except Exception as e:
        return bad(500, "SIGNUP_EXCEPTION", "Unexpected error during signup", str(e))

# ─────────────────────────────────────────────
# Login - Authenticate user with DynamoDB
# ─────────────────────────────────────────────
@router.post("/login")
def login(body: LoginBody):
    """
    Authenticate user with email and password
    """
    try:
        # Find user by email
        user = db.get_user_by_email(body.email)
        if not user:
            return bad(401, "INVALID_CREDENTIALS", "Invalid email or password")
        
        # Verify password
        if not user.get("password_hash"):
            return bad(401, "INVALID_CREDENTIALS", "Account not properly configured")
        
        if not verify_password(body.password, user["password_hash"]):
            return bad(401, "INVALID_CREDENTIALS", "Invalid email or password")
        
        # Generate JWT token
        token = sign_jwt({
            "id": user["id"],
            "email": user["email"],
            "role": "USER"
        })
        
        return ok("Login successful", {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"]
            }
        })
        
    except Exception as e:
        return bad(500, "LOGIN_EXCEPTION", "Unexpected error during login", str(e))
