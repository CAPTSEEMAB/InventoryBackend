#!/usr/bin/env python3
"""
Simple Manual End-to-End Test for Inventory API
Step-by-step testing with manual verification
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_step(step_name, func):
    """Test a single step"""
    print(f"\n🔧 {step_name}")
    print("-" * 50)
    try:
        result = func()
        if result:
            print(f"✅ {step_name} - SUCCESS")
        else:
            print(f"❌ {step_name} - FAILED")
        return result
    except Exception as e:
        print(f"❌ {step_name} - ERROR: {str(e)}")
        return False

def step1_check_server():
    """Step 1: Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        return False
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")
        return False

def step2_register_user():
    """Step 2: Register Safa user"""
    user_data = {
        "email": "safa@example.com",
        "password": "SafaTest123!",
        "phone_number": "+1234567890",
        "name": "Safa Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data, timeout=15)
        print(f"Registration Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return False

def step3_login_user():
    """Step 3: Login as Safa and get token"""
    login_data = {
        "username": "safa@example.com",
        "password": "SafaTest123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data, timeout=15)
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            if token:
                print(f"Token obtained: {token[:50]}...")
                return token
            else:
                print("No access token in response")
                print(f"Response: {response.text}")
        else:
            print(f"Login failed: {response.text}")
        return False
    except Exception as e:
        print(f"Login error: {str(e)}")
        return False

def step4_check_sqs_health(token):
    """Step 4: Check SQS health"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/sqs/health", headers=headers, timeout=10)
        print(f"SQS Health Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"SQS health check error: {str(e)}")
        return False

def step5_create_product(token):
    """Step 5: Create Safa's product"""
    headers = {"Authorization": f"Bearer {token}"}
    product_data = {
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
    
    try:
        response = requests.post(f"{BASE_URL}/api/products/", json=product_data, headers=headers, timeout=15)
        print(f"Product Creation Status: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            product_id = result.get("id")
            print(f"Product created with ID: {product_id}")
            print(f"Product details: {json.dumps(result, indent=2)}")
            return product_id
        else:
            print(f"Product creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"Product creation error: {str(e)}")
        return False

def step6_get_all_products(token):
    """Step 6: Get all products"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/products/", headers=headers, timeout=15)
        print(f"Get Products Status: {response.status_code}")
        if response.status_code == 200:
            products = response.json()
            print(f"Found {len(products)} products:")
            for i, product in enumerate(products[:3], 1):
                print(f"  {i}. {product.get('name', 'Unknown')} (SKU: {product.get('sku', 'N/A')})")
            return products
        else:
            print(f"Get products failed: {response.text}")
            return False
    except Exception as e:
        print(f"Get products error: {str(e)}")
        return False

def step7_test_sqs_notification(token):
    """Step 7: Send SQS notification"""
    headers = {"Authorization": f"Bearer {token}"}
    notification_data = {
        "message": "Safa's product notification test",
        "subject": "Product Update from Safa",
        "notification_type": "product_created",
        "metadata": {
            "user": "Safa",
            "product_name": "Safa's Premium Arabian Coffee",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/sqs/notification", json=notification_data, headers=headers, timeout=15)
        print(f"SQS Notification Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"SQS notification error: {str(e)}")
        return False

def main():
    """Run step-by-step tests"""
    print("🚀 Inventory Management API - Step-by-Step End-to-End Test")
    print("=" * 70)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests step by step
    token = None
    product_id = None
    
    if test_step("Check Server", step1_check_server):
        if test_step("Register Safa User", step2_register_user):
            token = test_step("Login Safa User", step3_login_user)
            
            if token:
                test_step("Check SQS Health", lambda: step4_check_sqs_health(token))
                product_id = test_step("Create Safa's Product", lambda: step5_create_product(token))
                test_step("Get All Products", lambda: step6_get_all_products(token))
                test_step("Send SQS Notification", lambda: step7_test_sqs_notification(token))
    
    print("\n" + "=" * 70)
    print("🎯 Manual testing completed!")
    print("📝 Check the output above for detailed results of each step")

if __name__ == "__main__":
    main()