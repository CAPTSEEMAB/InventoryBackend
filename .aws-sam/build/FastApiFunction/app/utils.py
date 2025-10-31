import os
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_EXPIRES_HOURS = 3

# Swagger-compatible bearer scheme
bearer_scheme = HTTPBearer(auto_error=False)

def ok(message: str = "OK", data=None, status_code: int = 200):
    return JSONResponse({"success": True, "message": message, "data": data}, status_code=status_code)

def bad(status_code: int, code: str, message: str, details=None):
    return JSONResponse({"success": False, "error": {"code": code, "message": message, "details": details}}, status_code=status_code)

def sign_jwt(payload: dict) -> str:
    exp = datetime.utcnow() + timedelta(hours=JWT_EXPIRES_HOURS)
    payload.update({"exp": exp})
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid token: {e}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = credentials.credentials
    return verify_jwt(token)
