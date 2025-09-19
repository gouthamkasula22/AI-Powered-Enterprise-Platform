#!/usr/bin/env python3
"""
Comprehensive RBAC System Testing Script

Tests the complete Role-Based Access Control implementation including:
- User registration and role assignment
- JWT token validation with roles
- Role-based endpoint protection
- Admin functionality
- Permission hierarchies
"""

import asyncio
import requests
import json
import sys
import time
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class TestUser:
    email: str
    password: str
    first_name: str
    last_name: str
    expected_role: str
    access_token: Optional[str] = None


class RBACSystemTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.test_results = []
        
        # Test users for different roles
        self.test_users = [
            TestUser("user@rbactest.com", "UserTest123!", "Test", "User", "USER"),
            TestUser("admin@rbactest.com", "AdminTest123!", "Test", "Admin", "ADMIN"),
            TestUser("superadmin@rbactest.com", "SuperTest123!", "Test", "SuperAdmin", "SUPERADMIN")
        ]
    
    def log_test(self, test_name: str, success: bool, message: str, details: Optional[dict] = None):
        """Log test results"""
        status = "PASS" if success else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        icon = "✅" if success else "❌"
        print(f"{icon} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_endpoint(self) -> bool:
        """Test basic API health"""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            success = response.status_code == 200
            
            self.log_test(
                "Health Check",
                success,
                f"API responding correctly" if success else f"API health check failed: {response.status_code}",
                {"status_code": response.status_code, "response": response.text[:200]}
            )
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def register_user(self, user: TestUser) -> bool:
        """Register a test user"""
        try:
            user_data = {
                "email": user.email,
                "password": user.password,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            response = requests.post(f"{self.api_base}/auth/register", json=user_data, timeout=10)
            
            if response.status_code in [200, 201]:
                self.log_test(
                    f"Register {user.expected_role} User",
                    True,
                    f"User {user.email} registered successfully"
                )
                return True
            elif response.status_code == 400:
                # Check if user already exists
                error_data = response.json()
                if "already exists" in str(error_data).lower():
                    self.log_test(
                        f"Register {user.expected_role} User",
                        True,
                        f"User {user.email} already exists (OK for testing)"
                    )
                    return True
                else:
                    self.log_test(
                        f"Register {user.expected_role} User",
                        False,
                        f"Registration failed: {error_data}",
                        {"status_code": response.status_code, "response": error_data}
                    )
                    return False
            else:
                self.log_test(
                    f"Register {user.expected_role} User",
                    False,
                    f"Registration failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return False
        except Exception as e:
            self.log_test(f"Register {user.expected_role} User", False, f"Registration error: {str(e)}")
            return False
    
    def login_user(self, user: TestUser) -> bool:
        """Login user and store access token"""
        try:
            login_data = {
                "email": user.email,
                "password": user.password
            }
            
            response = requests.post(f"{self.api_base}/auth/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user.access_token = data.get("access_token")
                user_role = data.get("user", {}).get("role", "UNKNOWN")
                
                self.log_test(
                    f"Login {user.expected_role} User",
                    True,
                    f"Login successful for {user.email} (Role: {user_role})",
                    {"role": user_role, "has_token": bool(user.access_token)}
                )
                return True
            else:
                self.log_test(
                    f"Login {user.expected_role} User",
                    False,
                    f"Login failed: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return False
        except Exception as e:
            self.log_test(f"Login {user.expected_role} User", False, f"Login error: {str(e)}")
            return False
    
    def test_endpoint_access(self, endpoint: str, user: TestUser, expected_status: int, test_name: str) -> bool:
        """Test endpoint access with user's token"""
        try:
            headers = {}
            if user.access_token:
                headers["Authorization"] = f"Bearer {user.access_token}"
            
            response = requests.get(f"{self.api_base}{endpoint}", headers=headers, timeout=10)
            success = response.status_code == expected_status
            
            details = {
                "endpoint": endpoint,
                "user_role": user.expected_role,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "has_auth": bool(user.access_token)
            }
            
            if success:
                message = f"Correct access control (Status: {response.status_code})"
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "message" in data:
                            details["response_message"] = data["message"]
                    except:
                        pass
            else:
                message = f"Access control failed - Expected {expected_status}, got {response.status_code}"
                details["response"] = response.text[:200]
            
            self.log_test(test_name, success, message, details)
            return success
            
        except Exception as e:
            self.log_test(test_name, False, f"Request error: {str(e)}")
            return False
    
    def test_jwt_payload(self, user: TestUser) -> bool:
        """Test JWT token contains role information"""
        if not user.access_token:
            self.log_test(f"JWT Payload Test ({user.expected_role})", False, "No access token available")
            return False
        
        try:
            # Decode JWT payload (just the payload part, not verifying signature)
            import base64
            
            # Split token and get payload
            parts = user.access_token.split('.')
            if len(parts) != 3:
                self.log_test(f"JWT Payload Test ({user.expected_role})", False, "Invalid JWT format")
                return False
            
            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            jwt_data = json.loads(decoded)
            
            # Check for role information
            has_role = 'role' in jwt_data
            has_permissions = 'permissions' in jwt_data
            role_value = jwt_data.get('role', 'MISSING')
            
            success = has_role and has_permissions
            
            details = {
                "has_role_field": has_role,
                "has_permissions_field": has_permissions,
                "role_value": role_value,
                "expected_role": user.expected_role,
                "jwt_payload": jwt_data
            }
            
            message = f"JWT contains role and permissions" if success else f"JWT missing role/permissions fields"
            
            self.log_test(f"JWT Payload Test ({user.expected_role})", success, message, details)
            return success
            
        except Exception as e:
            self.log_test(f"JWT Payload Test ({user.expected_role})", False, f"JWT decode error: {str(e)}")
            return False
    
    def run_comprehensive_tests(self) -> Dict:
        """Run all RBAC tests"""
        print("🔧 Starting Comprehensive RBAC System Tests")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        # Test 1: Basic connectivity
        print("\n📡 Test Suite 1: Basic Connectivity")
        print("-" * 40)
        
        if self.test_health_endpoint():
            passed_tests += 1
        total_tests += 1
        
        # Test 2: User registration
        print("\n👤 Test Suite 2: User Registration")
        print("-" * 40)
        
        for user in self.test_users:
            if self.register_user(user):
                passed_tests += 1
            total_tests += 1
        
        # Test 3: User authentication
        print("\n🔐 Test Suite 3: User Authentication")
        print("-" * 40)
        
        for user in self.test_users:
            if self.login_user(user):
                passed_tests += 1
            total_tests += 1
        
        # Test 4: JWT payload validation
        print("\n🎫 Test Suite 4: JWT Token Validation")
        print("-" * 40)
        
        for user in self.test_users:
            if self.test_jwt_payload(user):
                passed_tests += 1
            total_tests += 1
        
        # Test 5: Role-based access control
        print("\n🛡️ Test Suite 5: Role-Based Access Control")
        print("-" * 40)
        
        # Define test cases: (endpoint, user_index, expected_status, test_description)
        access_tests = [
            # Unauthenticated access
            ("/admin/dashboard", None, 401, "Unauthenticated admin access"),
            ("/admin/superadmin", None, 401, "Unauthenticated superadmin access"),
            
            # USER role access
            ("/admin/test/role-check", 0, 200, "USER accessing role check"),
            ("/admin/dashboard", 0, 403, "USER accessing admin dashboard"),
            ("/admin/superadmin", 0, 403, "USER accessing superadmin panel"),
            
            # ADMIN role access
            ("/admin/test/role-check", 1, 200, "ADMIN accessing role check"),
            ("/admin/dashboard", 1, 200, "ADMIN accessing admin dashboard"),
            ("/admin/superadmin", 1, 403, "ADMIN accessing superadmin panel"),
            
            # SUPERADMIN role access
            ("/admin/test/role-check", 2, 200, "SUPERADMIN accessing role check"),
            ("/admin/dashboard", 2, 200, "SUPERADMIN accessing admin dashboard"),
            ("/admin/superadmin", 2, 200, "SUPERADMIN accessing superadmin panel"),
        ]
        
        for endpoint, user_index, expected_status, description in access_tests:
            user = self.test_users[user_index] if user_index is not None else TestUser("", "", "", "", "NONE")
            
            if self.test_endpoint_access(endpoint, user, expected_status, description):
                passed_tests += 1
            total_tests += 1
        
        # Test 6: RBAC demonstration endpoints
        print("\n🎭 Test Suite 6: RBAC Demonstration")
        print("-" * 40)
        
        demo_tests = [
            ("/admin/test/rbac-demo", 0, 200, "USER accessing RBAC demo"),
            ("/admin/test/rbac-demo", 1, 200, "ADMIN accessing RBAC demo"),
            ("/admin/test/rbac-demo", 2, 200, "SUPERADMIN accessing RBAC demo"),
        ]
        
        for endpoint, user_index, expected_status, description in demo_tests:
            user = self.test_users[user_index]
            
            if self.test_endpoint_access(endpoint, user, expected_status, description):
                passed_tests += 1
            total_tests += 1
        
        # Calculate results
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 RBAC System is working excellently!")
        elif success_rate >= 75:
            print("\n✅ RBAC System is working well with minor issues")
        elif success_rate >= 50:
            print("\n⚠️ RBAC System has significant issues")
        else:
            print("\n❌ RBAC System has critical failures")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "detailed_results": self.test_results
        }
    
    def save_test_report(self, results: Dict, filename: str = "rbac_test_report.json"):
        """Save detailed test report to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Detailed test report saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️ Failed to save test report: {e}")


def main():
    """Main test execution"""
    print("🔧 RBAC System Comprehensive Testing Tool")
    print("Testing against: http://127.0.0.1:8000")
    print("This will validate the complete RBAC implementation\n")
    
    tester = RBACSystemTester()
    
    try:
        results = tester.run_comprehensive_tests()
        tester.save_test_report(results)
        
        # Exit with appropriate code
        if results["success_rate"] >= 90:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()