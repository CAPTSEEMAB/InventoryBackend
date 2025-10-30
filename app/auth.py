import os
from fastapi import APIRouter
from pydantic import BaseModel
from supabase import create_client, Client
from .utils import ok, bad, sign_jwt

# ─────────────────────────────────────────────
# Supabase client setup
# ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SERVICE_ROLE or not ANON_KEY:
    raise RuntimeError("Missing Supabase configuration in .env")

db: Client = create_client(SUPABASE_URL, SERVICE_ROLE)
dbAnon: Client = create_client(SUPABASE_URL, ANON_KEY)

router = APIRouter(prefix="/auth", tags=["Auth"])

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
# Signup (always requires email confirmation)
# ─────────────────────────────────────────────
@router.post("/signup")
def signup(body: SignupBody):
    """
    Sends a confirmation email through Supabase Auth.
    The user must confirm before they can log in.
    """
    try:
        resp = dbAnon.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {
                "data": {"full_name": body.name}
            }
        })

        user = getattr(resp, "user", None)
        error = getattr(resp, "error", None)
        if error:
            return bad(400, "SIGNUP_FAILED", str(error))

        return ok(
            "Signup successful — please check your email to confirm your account.",
            {
                "user": {
                    "id": getattr(user, "id", None),
                    "email": body.email,
                    "name": body.name
                },
                "email_sent": True,
                "next_step": "Confirm your email before logging in."
            }
        )
    except Exception as e:
        return bad(500, "SIGNUP_EXCEPTION", "Unexpected error during signup", str(e))

# ─────────────────────────────────────────────
# Login (fails if email not confirmed)
# ─────────────────────────────────────────────
@router.post("/login")
def login(body: LoginBody):
    """
    Only confirmed users can log in.
    Supabase automatically blocks unconfirmed users.
    """
    try:
        resp = dbAnon.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })

        user = getattr(resp, "user", None)
        error = getattr(resp, "error", None)

        if error or not user:
            msg = str(error) if error else "Invalid credentials"
            if "Email not confirmed" in msg or "confirmation" in msg.lower():
                return bad(401, "EMAIL_NOT_CONFIRMED", "Email not confirmed. Please check your inbox.")
            return bad(401, "INVALID_CREDENTIALS", msg)

        token = sign_jwt({
            "id": user.id,
            "email": user.email,
            "role": "USER"
        })

        return ok("Login successful", {
            "token": token,
            "user": {"id": user.id, "email": user.email}
        })

    except Exception as e:
        return bad(500, "LOGIN_EXCEPTION", "Unexpected error during login", str(e))
