"""
Utility functions for the Inventory API
Simplified version without custom JWT - uses AWS Cognito only
"""

import os
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

def ok(message: str = "OK", data=None, status_code: int = 200):
    """Return success response"""
    return JSONResponse({
        "success": True, 
        "message": message, 
        "data": data
    }, status_code=status_code)

def bad(status_code: int, code: str, message: str, details=None):
    """Return error response"""
    return JSONResponse({
        "success": False, 
        "error": {
            "code": code, 
            "message": message, 
            "details": details
        }
    }, status_code=status_code)

def get_env_var(key: str, default: str = None, required: bool = False):
    """Get environment variable with optional validation"""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None