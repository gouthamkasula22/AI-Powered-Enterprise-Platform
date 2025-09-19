#!/usr/bin/env python3
"""
RBAC System Validation Script

Tests the RBAC implementation by making HTTP requests to the endpoints.
This validates that role-based access control is working properly.
"""

import requests
import json
import sys
from typing import Dict, Optional


class RBACTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        
    def test_health_endpoint(self) -> bool:
        """Test basic health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health endpoint accessible")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    def register_test_user(self, email: str, password: str, first_name: str, last_name: str) -> bool:
        """Register a test user"""
        try:
            user_data = {
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name
            }
            
            response = requests.post(f"{self.api_base}/auth/register", json=user_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ User registered successfully: {email}")
                return True
            elif response.status_code == 400:
                # User might already exist
                data = response.json()
                if "already exists" in str(data):
                    print(f"ℹ️ User already exists: {email}")
                    return True
                else:
                    print(f"❌ Registration failed: {data}")
                    return False
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def login_user(self, email: str, password: str) -> Optional[str]:
        """Login user and return access token"""
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            response = requests.post(f"{self.api_base}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                user_role = data.get("user", {}).get("role", "UNKNOWN")
                print(f"✅ Login successful: {email} (Role: {user_role})")
                return access_token
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None
    
    def test_endpoint_access(self, endpoint: str, token: Optional[str], expected_status: int, description: str) -> bool:
        """Test endpoint access with token"""
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = requests.get(f"{self.api_base}{endpoint}", headers=headers)
            
            if response.status_code == expected_status:
                print(f"✅ {description}: Expected {expected_status}, got {response.status_code}")
                if response.status_code == 200:
                    # Print some response data for successful requests
                    data = response.json()
                    if isinstance(data, dict) and "message" in data:
                        print(f"   Response: {data['message']}")
                return True
            else:
                print(f"❌ {description}: Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ {description} error: {e}")
            return False
    
    def run_rbac_tests(self) -> bool:
        """Run comprehensive RBAC tests"""
        print("🚀 Starting RBAC System Validation")
        print("=" * 60)
        
        # Test 1: Basic connectivity
        print("\n📡 Test 1: Basic Connectivity")
        print("-" * 40)
        if not self.test_health_endpoint():
            return False
        
        # Test 2: User registration
        print("\n👤 Test 2: User Registration")
        print("-" * 40)
        
        test_users = [
            {
                "email": "testuser@example.com",
                "password": "TestUser123!",
                "first_name": "Test",
                "last_name": "User"
            },
            {
                "email": "testadmin@example.com", 
                "password": "TestAdmin123!",
                "first_name": "Test",
                "last_name": "Admin"
            }
        ]
        
        for user in test_users:
            if not self.register_test_user(**user):
                return False
        
        # Test 3: User authentication
        print("\n🔐 Test 3: User Authentication")
        print("-" * 40)
        
        user_token = self.login_user("testuser@example.com", "TestUser123!")
        admin_token = self.login_user("testadmin@example.com", "TestAdmin123!")
        
        if not user_token:
            print("❌ Failed to get user token")
            return False
        if not admin_token:
            print("❌ Failed to get admin token")
            return False
        
        # Test 4: Role-based endpoint access
        print("\n🛡️ Test 4: Role-Based Endpoint Access")
        print("-" * 40)
        
        # Test unauthenticated access (should fail)
        if not self.test_endpoint_access("/admin/dashboard", None, 401, "Unauthenticated admin access"):
            return False
        
        # Test authenticated user access to admin endpoint (should fail)
        if not self.test_endpoint_access("/admin/dashboard", user_token, 403, "User trying admin access"):
            return False
        
        # Test admin access to admin endpoint (should succeed)
        if not self.test_endpoint_access("/admin/dashboard", admin_token, 200, "Admin accessing admin endpoint"):
            return False
        
        # Test role checking endpoint (should work for both)
        if not self.test_endpoint_access("/admin/test/role-check", user_token, 200, "User role check"):
            return False
        
        if not self.test_endpoint_access("/admin/test/role-check", admin_token, 200, "Admin role check"):
            return False
        
        # Test 5: RBAC demonstration
        print("\n🎭 Test 5: RBAC Demonstration")
        print("-" * 40)
        
        if not self.test_endpoint_access("/admin/test/rbac-demo", user_token, 200, "RBAC demo for user"):
            return False
        
        if not self.test_endpoint_access("/admin/test/rbac-demo", admin_token, 200, "RBAC demo for admin"):
            return False
        
        print("\n🎉 RBAC System Validation Complete!")
        print("=" * 60)
        print("✅ All tests passed successfully!")
        print("\nRBAC System is working correctly:")
        print("  ✓ User registration and authentication")
        print("  ✓ JWT token generation with roles")
        print("  ✓ Role-based endpoint protection")
        print("  ✓ Proper access control enforcement")
        print("  ✓ Admin endpoints accessible to admins only")
        
        return True


def main():
    """Main test function"""
    tester = RBACTester()
    
    print("🔧 RBAC System Validation Tool")
    print(f"Testing against: {tester.api_base}")
    print("This will test the complete RBAC implementation")
    print()
    
    # Run the tests
    success = tester.run_rbac_tests()
    
    if success:
        print("\n🚀 RBAC system is fully functional!")
        print("\nYou can now:")
        print("  1. Access the API docs at: http://127.0.0.1:8000/docs")
        print("  2. Test endpoints manually using the Swagger UI")
        print("  3. Integrate the frontend with role-based components")
        print("  4. Create users with different roles for testing")
        sys.exit(0)
    else:
        print("\n💥 RBAC system validation failed!")
        print("Check the error messages above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()