import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from . import auth
from . import products
from . import profiles
from .utils import ok, bad
from .dynamodb_client import get_db_client

# Force-load .env
ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

PORT = int(os.getenv("PORT", 3000))
API_PREFIX = os.getenv("API", "/api")

app = FastAPI(
    title="Inventory Shop API",
    description="Full CRUD + Auth using FastAPI & AWS DynamoDB",
    version="1.0.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
)

# Add JWT Bearer security scheme to OpenAPI docs
from fastapi.openapi.utils import get_openapi
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for op in path.values():
            if isinstance(op, dict):
                op["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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
        "auth": [f"{API_PREFIX}/auth/signup", f"{API_PREFIX}/auth/login"],
        "profiles": [f"{API_PREFIX}/profiles/me"],
        "products": [
            f"{API_PREFIX}/products", 
            f"{API_PREFIX}/products/{{id}}", 
            f"{API_PREFIX}/products/by-category/{{category}}",
            f"{API_PREFIX}/products/by-sku/{{sku}}"
        ],
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

# Startup probe and DynamoDB health check
@app.on_event("startup")
async def startup_probe():
    try:
        print("🟡 Checking DynamoDB connection...")
        db = get_db_client()
        health = db.health_check()
        
        if health['status'] == 'healthy':
            print(f"✅ {health['user_profiles']}")
            print(f"✅ {health['inventory_products']}")
            print(f"✅ Region: {health['region']}")
        else:
            print(f"❌ DynamoDB health check failed: {health.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Startup check failed: {e}")
        print("⚠️  Application will continue but database operations may fail")


# For AWS Lambda + API Gateway integration (if needed)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # Mangum not available, skip Lambda handler
    pass