import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from . import auth, products, s3_routes, sqs_routes
from .utils import ok, bad
from .dynamodb_client import get_db_client

ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

PORT = int(os.getenv("PORT", 8000))
API_PREFIX = os.getenv("API_PREFIX", "/api")

app = FastAPI(
    title="Inventory Shop API",
    description="Full CRUD + Auth using FastAPI & AWS DynamoDB",
    version="1.0.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
)

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
        "s3": [
            f"{API_PREFIX}/s3",
            f"{API_PREFIX}/s3/upload",
            f"{API_PREFIX}/s3/files",
            f"{API_PREFIX}/s3/download/{{file_key}}",
            f"{API_PREFIX}/s3/stats"
        ],
        "sqs": [
            f"{API_PREFIX}/sqs",
            f"{API_PREFIX}/sqs/stats",
            f"{API_PREFIX}/sqs/notification",
            f"{API_PREFIX}/sqs/worker/stats",
            f"{API_PREFIX}/sqs/health"
        ],
        "docs": f"{API_PREFIX}/docs",
    })

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(s3_routes.router, prefix=API_PREFIX)
app.include_router(sqs_routes.router, prefix=API_PREFIX)

@app.exception_handler(Exception)
async def on_exception(_req: Request, exc: Exception):
    return bad(500, "SERVER_ERROR", "Something went wrong", str(exc))

@app.on_event("startup")
async def startup_probe():
    # Simplified startup - services will be initialized on first use
    pass


@app.on_event("shutdown")
async def shutdown_probe():
    try:
        from .sqs.worker import stop_background_worker
        stop_background_worker()
    except Exception as e:
        pass


try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    pass