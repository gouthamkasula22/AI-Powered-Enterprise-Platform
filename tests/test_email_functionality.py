#!/usr/bin/env python3
"""
Comprehensive Email Functionality Testing Script

This script tests all email-related functionality including:
- Email verification flow
- Password reset flow
- Email service endpoints
- Frontend-backend integration

Usage: python tests/test_email_functionality.py
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_EMAIL = f"test_{int(time.time())}@example.com"  # Unique email each run
TEST_PASSWORD = "TestPassword123!"

class EmailFunctionalityTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
    def test_backend_health(self) -> bool:
        """Test if backend is running and healthy"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log_test("Backend Health", "PASS", "Backend is running")
                return True
            else:
                self.log_test("Backend Health", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_email_validation_endpoint(self) -> bool:
        """Test email validation API endpoint"""
        try:
            # Test valid email
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/validate-email",
                json={"email": "valid@example.com"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("is_valid"):
                    self.log_test("Email Validation - Valid", "PASS", "Valid email accepted")
                else:
                    self.log_test("Email Validation - Valid", "FAIL", f"Valid email rejected: {data}")
                    return False
            else:
                self.log_test("Email Validation - Valid", "FAIL", f"Status: {response.status_code}")
                return False
                
            # Test invalid email
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/validate-email",
                json={"email": "invalid-email"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("is_valid"):
                    self.log_test("Email Validation - Invalid", "PASS", "Invalid email rejected")
                else:
                    self.log_test("Email Validation - Invalid", "FAIL", "Invalid email accepted")
                    return False
            else:
                self.log_test("Email Validation - Invalid", "FAIL", f"Status: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("Email Validation", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_password_validation_endpoint(self) -> bool:
        """Test password validation API endpoint"""
        try:
            # Test strong password
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/validate-password",
                json={"password": "StrongPassword123!", "email": "test@example.com"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("is_valid"):
                    self.log_test("Password Validation - Strong", "PASS", f"Strength: {data.get('strength_level')}")
                else:
                    self.log_test("Password Validation - Strong", "FAIL", f"Strong password rejected: {data}")
                    return False
            else:
                self.log_test("Password Validation - Strong", "FAIL", f"Status: {response.status_code}")
                return False
                
            # Test weak password
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/validate-password",
                json={"password": "123", "email": "test@example.com"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("is_valid"):
                    self.log_test("Password Validation - Weak", "PASS", "Weak password rejected")
                else:
                    self.log_test("Password Validation - Weak", "FAIL", "Weak password accepted")
                    return False
            else:
                self.log_test("Password Validation - Weak", "FAIL", f"Status: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("Password Validation", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_user_registration(self) -> bool:
        """Test user registration with email verification"""
        try:
            # Register new user
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log_test("User Registration", "PASS", f"User registered: {data.get('message')}")
                return True
            elif response.status_code == 400:
                data = response.json()
                if "already exists" in data.get("detail", "").lower():
                    self.log_test("User Registration", "PASS", "User already exists (expected)")
                    return True
                else:
                    self.log_test("User Registration", "FAIL", f"Registration failed: {data}")
                    return False
            else:
                self.log_test("User Registration", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_forgot_password_flow(self) -> bool:
        """Test forgot password flow"""
        try:
            # Request password reset
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/forgot-password",
                json={"email": TEST_EMAIL}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Forgot Password Request", "PASS", f"Reset email requested: {data.get('message')}")
                return True
            else:
                self.log_test("Forgot Password Request", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Forgot Password Request", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_resend_verification(self) -> bool:
        """Test resend verification email"""
        try:
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/resend-verification",
                json={"email": TEST_EMAIL}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Resend Verification", "PASS", f"Verification email resent: {data.get('message')}")
                return True
            else:
                self.log_test("Resend Verification", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Resend Verification", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_frontend_accessibility(self) -> bool:
        """Test if frontend pages are accessible"""
        try:
            # Test main pages
            pages = [
                "/",
                "/login", 
                "/register",
                "/forgot-password"
            ]
            
            for page in pages:
                try:
                    response = self.session.get(f"{FRONTEND_URL}{page}")
                    if response.status_code == 200:
                        self.log_test(f"Frontend Page {page}", "PASS", "Page accessible")
                    else:
                        self.log_test(f"Frontend Page {page}", "FAIL", f"Status: {response.status_code}")
                        return False
                except Exception as e:
                    self.log_test(f"Frontend Page {page}", "FAIL", f"Error: {str(e)}")
                    return False
                    
            return True
            
        except Exception as e:
            self.log_test("Frontend Accessibility", "FAIL", f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all email functionality tests"""
        print("=" * 60)
        print("STARTING EMAIL FUNCTIONALITY TESTS")
        print("=" * 60)
        
        tests = [
            self.test_backend_health,
            self.test_email_validation_endpoint,
            self.test_password_validation_endpoint,
            self.test_user_registration,
            self.test_forgot_password_flow,
            self.test_resend_verification,
            self.test_frontend_accessibility
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
                
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
        
        # Save detailed results
        with open("tests/email_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\nDetailed results saved to: tests/email_test_results.json")
        
        return failed == 0

if __name__ == "__main__":
    tester = EmailFunctionalityTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n⚠️  Some tests failed. Check the results for details.")
        exit(1)
    else:
        print("\n✅ All tests passed!")
        exit(0)
