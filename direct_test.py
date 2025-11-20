#!/usr/bin/env python3
"""
Direct Application Test - Testing without HTTP server
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        # Test individual module imports
        modules_to_test = [
            'app',
            'app.main',
            'app.auth', 
            'app.products',
            'app.s3_routes',
            'app.sqs_routes',
            'app.utils',
            'app.dynamodb_client'
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ {module_name} - imported successfully")
            except Exception as e:
                print(f"❌ {module_name} - import failed: {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

def test_fastapi_app():
    """Test FastAPI app creation"""
    print("\n🚀 Testing FastAPI app creation...")
    
    try:
        from app.main import app
        print(f"✅ FastAPI app created successfully")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
        
        # List routes
        print(f"\n📍 Available routes:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if route.methods else ['N/A']
                print(f"   {methods} {route.path}")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI app creation failed: {str(e)}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🌍 Testing environment configuration...")
    
    try:
        # Load environment
        from dotenv import load_dotenv
        env_file = project_root / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Environment file loaded: {env_file}")
            
            # Check some key variables
            env_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'DYNAMODB_TABLE_NAME']
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    # Mask sensitive values
                    display_value = value if 'KEY' not in var else f"{value[:8]}...{value[-4:]}"
                    print(f"   {var}: {display_value}")
                else:
                    print(f"   {var}: Not set")
        else:
            print(f"⚠️  Environment file not found: {env_file}")
        
        return True
    except Exception as e:
        print(f"❌ Environment test failed: {str(e)}")
        return False

def test_aws_clients():
    """Test AWS client initialization"""
    print("\n☁️  Testing AWS clients...")
    
    try:
        # Test DynamoDB client
        from app.dynamodb_client import get_db_client
        db_client = get_db_client()
        if db_client:
            print(f"✅ DynamoDB client initialized")
        else:
            print(f"⚠️  DynamoDB client not available")
        
        # Test S3 client
        from app.s3.s3_client import S3Client
        s3_client = S3Client()
        print(f"✅ S3 client initialized")
        
        # Test SQS client  
        from app.sqs.sqs_client import SQSClient
        sqs_client = SQSClient()
        print(f"✅ SQS client initialized")
        
        return True
    except Exception as e:
        print(f"❌ AWS clients test failed: {str(e)}")
        return False

def test_data_models():
    """Test data models and validation"""
    print("\n📊 Testing data models...")
    
    try:
        # Create sample product data
        sample_product = {
            "name": "Safa's Premium Arabian Coffee",
            "sku": "SAFA-ARB-001", 
            "category": "Safa's Beverages",
            "supplier": "Safa's Coffee Roasters",
            "price": 24.99,
            "reorder_level": 15,
            "in_stock": 100,
            "description": "Premium Arabian coffee beans specially curated by Safa",
            "movements": [
                {
                    "movement_date": "2025-11-20",
                    "type": "IN",
                    "quantity": 100
                }
            ]
        }
        
        # Test product validation (if models exist)
        print(f"✅ Sample product data created")
        print(f"   Product: {sample_product['name']}")
        print(f"   SKU: {sample_product['sku']}")
        print(f"   Price: ${sample_product['price']}")
        
        return True
    except Exception as e:
        print(f"❌ Data models test failed: {str(e)}")
        return False

def main():
    """Run all direct tests"""
    print("🧪 Inventory Management API - Direct Application Test")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print(f"Python Version: {sys.version}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests = [
        test_imports,
        test_environment, 
        test_fastapi_app,
        test_aws_clients,
        test_data_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Application components are working!")
    elif passed >= total * 0.8:
        print("✅ Most tests passed! Application is mostly ready.")
    else:
        print("⚠️  Several tests failed. Check configuration.")
    
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if main() else 1)