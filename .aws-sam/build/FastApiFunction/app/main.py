# For AWS Lambda + API Gateway integration
from mangum import Mangum
# Expose handler for AWS Lambda
handler = Mangum(app)
import os
import json
import base64
import boto3
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from . import auth, products, profiles
from .utils import ok, bad

# Force-load .env
ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

PORT = int(os.getenv("PORT", 3000))
API_PREFIX = os.getenv("API", "/api")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

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


# Startup probe and DynamoDB table creation
@app.on_event("startup")
async def startup_probe():
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        def ensure_table(table_name, key_name):
            existing_tables = [t.name for t in dynamodb.tables.all()]
            if table_name in existing_tables:
                print(f"✅ Table '{table_name}' already exists.")
                return
            print(f"🟡 Creating table '{table_name}'...")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": key_name, "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": key_name, "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST"
            )
            table.wait_until_exists()
            print(f"✅ Table '{table_name}' created.")
        ensure_table("user_profiles", "id")
        ensure_table("inventory_products", "id")
    except Exception as e:
        print(f"❌ Startup check failed: {e}")


        
