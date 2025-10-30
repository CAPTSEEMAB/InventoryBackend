import os, json, base64
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from supabase import create_client
from . import auth, products, profiles
from .utils import ok, bad

# Force-load .env
ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

PORT = int(os.getenv("PORT", 3000))
API_PREFIX = os.getenv("API", "/api")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

app = FastAPI(
    title="Inventory Shop API",
    description="Full CRUD + Auth using FastAPI & Supabase",
    version="1.0.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root_redirect():
    return RedirectResponse(url=f"{API_PREFIX}/docs")

@app.get(f"{API_PREFIX}/")
def index():
    return ok("Inventory Shop API", {
        "auth": [f"{API_PREFIX}/auth/signup", f"{API_PREFIX}/auth/login", f"{API_PREFIX}/auth/me"],
        "profiles": [f"{API_PREFIX}/profiles/me"],
        "products": [f"{API_PREFIX}/products", f"{API_PREFIX}/products/{{id}}?days=30"],
        "docs": f"{API_PREFIX}/docs",
    })

# Include routers
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(profiles.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)

# Error handler
@app.exception_handler(Exception)
async def on_exception(_req: Request, exc: Exception):
    print("Unhandled error:", repr(exc))
    return bad(500, "SERVER_ERROR", "Something went wrong", str(exc))

# Startup probe
@app.on_event("startup")
async def startup_probe():
    try:
        url = os.getenv("SUPABASE_URL", "")
        srk = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        sb = create_client(url, srk)
        print("🟡 Checking Supabase tables...")
        for t in ["user_profiles", "inventory_products"]:
            try:
                r = sb.table(t).select("id").limit(1).execute()
                print(f"✅ {t}: {len(r.data)} rows accessible")
            except Exception as e:
                print(f"⚠️  {t}: {e}")
    except Exception as e:
        print(f"❌ Startup check failed: {e}")
