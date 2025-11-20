#!/usr/bin/env python3
"""
HTTP Server Test with proper startup handling
"""

import os
import sys
import time
import signal
import subprocess
import requests
import json
from pathlib import Path
from datetime import datetime

class ServerTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.server_process = None
        
    def start_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting FastAPI server...")
        
        try:
            # Change to project directory
            project_dir = Path(__file__).parent
            os.chdir(project_dir)
            
            # Start server process
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", "127.0.0.1", 
                "--port", "8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            max_attempts = 20
            for attempt in range(max_attempts):
                try:
                    response = requests.get(f"{self.base_url}/api/", timeout=2)
                    if response.status_code == 200:
                        print(f"✅ Server started successfully (attempt {attempt + 1})")
                        return True
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(1)
                
                # Check if process is still running
                if self.server_process.poll() is not None:
                    stdout, stderr = self.server_process.communicate()
                    print(f"❌ Server process died:")
                    print(f"STDOUT: {stdout.decode()}")
                    print(f"STDERR: {stderr.decode()}")
                    return False
            
            print(f"❌ Server failed to start after {max_attempts} attempts")
            return False
            
        except Exception as e:
            print(f"❌ Error starting server: {str(e)}")
            return False
    
    def stop_server(self):
        """Stop the server"""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
            print("✅ Server stopped")
    
    def test_endpoint(self, method, path, data=None, headers=None, expected_status=200):
        """Test a specific endpoint"""
        url = f"{self.base_url}{path}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, f"Unsupported method: {method}"
            
            success = response.status_code == expected_status
            return success, {
                "status": response.status_code,
                "response": response.text[:500] if response.text else "No response body"
            }
        except Exception as e:
            return False, str(e)
    
    def run_comprehensive_test(self):
        """Run comprehensive end-to-end tests"""
        print("🧪 Running Comprehensive HTTP API Tests")
        print("=" * 60)
        
        # Test data
        user_data = {
            "email": "safa@example.com",
            "password": "SafaTest123!",
            "phone_number": "+1234567890",
            "name": "Safa Test User"
        }
        
        product_data = {
            "name": "Safa's Premium Arabian Coffee",
            "sku": "SAFA-ARB-001",
            "category": "Safa's Beverages",
            "supplier": "Safa's Coffee Roasters",
            "price": 24.99,
            "reorder_level": 15,
            "in_stock": 100,
            "description": "Premium Arabian coffee beans specially curated by Safa",
            "movements": [{
                "movement_date": "2025-11-20",
                "type": "IN",
                "quantity": 100
            }]
        }
        
        # Test sequence
        tests = []
        access_token = None
        product_id = None
        
        # 1. Test API Index
        print("\\n🔍 Test 1: API Index")
        success, result = self.test_endpoint("GET", "/api/")
        if success:
            print("✅ API Index - SUCCESS")
            print(f"   Response preview: {result['response'][:100]}...")
        else:
            print(f"❌ API Index - FAILED: {result}")
        tests.append(success)
        
        # 2. Test User Registration
        print("\\n👤 Test 2: User Registration (Safa)")
        success, result = self.test_endpoint("POST", "/api/auth/signup", data=user_data, expected_status=200)
        if success:
            print("✅ User Registration - SUCCESS")
        else:
            print(f"❌ User Registration - FAILED: {result}")
        tests.append(success)
        
        # 3. Test User Login
        print("\\n🔐 Test 3: User Login")
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        success, result = self.test_endpoint("POST", "/api/auth/login", data=login_data)
        if success:
            try:
                response_data = json.loads(result['response'])
                access_token = response_data.get("access_token")
                if access_token:
                    print("✅ User Login - SUCCESS")
                    print(f"   Token obtained: {access_token[:30]}...")
                else:
                    print("❌ User Login - No access token in response")
                    success = False
            except json.JSONDecodeError:
                print("❌ User Login - Invalid JSON response")
                success = False
        else:
            print(f"❌ User Login - FAILED: {result}")
        tests.append(success)
        
        # Continue tests only if we have a token
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 4. Test SQS Health
            print("\\n📡 Test 4: SQS Health Check")
            success, result = self.test_endpoint("GET", "/api/sqs/health", headers=headers)
            if success:
                print("✅ SQS Health Check - SUCCESS")
            else:
                print(f"❌ SQS Health Check - FAILED: {result}")
            tests.append(success)
            
            # 5. Test Product Creation
            print("\\n🛍️  Test 5: Create Product (Safa's Coffee)")
            success, result = self.test_endpoint("POST", "/api/products/", data=product_data, headers=headers, expected_status=201)
            if success:
                try:
                    response_data = json.loads(result['response'])
                    product_id = response_data.get("id")
                    print("✅ Product Creation - SUCCESS")
                    print(f"   Product ID: {product_id}")
                except json.JSONDecodeError:
                    print("✅ Product Creation - SUCCESS (could not parse ID)")
            else:
                print(f"❌ Product Creation - FAILED: {result}")
            tests.append(success)
            
            # 6. Test Get All Products
            print("\\n📋 Test 6: Get All Products")
            success, result = self.test_endpoint("GET", "/api/products/", headers=headers)
            if success:
                try:
                    products = json.loads(result['response'])
                    if isinstance(products, list):
                        print(f"✅ Get All Products - SUCCESS ({len(products)} products)")
                        for i, product in enumerate(products[:3], 1):
                            name = product.get('name', 'Unknown') if isinstance(product, dict) else str(product)
                            print(f"   {i}. {name}")
                    else:
                        print("✅ Get All Products - SUCCESS")
                except json.JSONDecodeError:
                    print("✅ Get All Products - SUCCESS (could not parse response)")
            else:
                print(f"❌ Get All Products - FAILED: {result}")
            tests.append(success)
            
            # 7. Test SQS Notification
            print("\\n🔔 Test 7: Send SQS Notification")
            notification_data = {
                "message": "Safa's product notification test",
                "subject": "Product Update from Safa",
                "notification_type": "product_created"
            }
            success, result = self.test_endpoint("POST", "/api/sqs/notification", data=notification_data, headers=headers)
            if success:
                print("✅ SQS Notification - SUCCESS")
            else:
                print(f"❌ SQS Notification - FAILED: {result}")
            tests.append(success)
            
        else:
            print("⚠️  Skipping remaining tests - no access token")
            # Add failed tests for remaining
            tests.extend([False] * 4)
        
        # Summary
        passed = sum(tests)
        total = len(tests)
        
        print("\\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Full end-to-end functionality confirmed!")
        elif passed >= total * 0.8:
            print("✅ Most tests passed! Application is highly functional.")
        else:
            print("⚠️  Several tests failed. Check application configuration.")
        
        return passed == total

def main():
    """Main execution"""
    tester = ServerTester()
    
    try:
        if tester.start_server():
            print("\\n⏳ Allowing server to fully initialize...")
            time.sleep(3)
            
            success = tester.run_comprehensive_test()
            return 0 if success else 1
        else:
            print("❌ Failed to start server")
            return 1
    finally:
        tester.stop_server()

if __name__ == "__main__":
    sys.exit(main())