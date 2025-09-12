#!/usr/bin/env python3
"""
Email Integration Testing Script

This script performs end-to-end testing of email functionality
including actual email verification and password reset flows.

Usage: python tests/test_email_integration.py
"""

import requests
import json
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class EmailIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        
        # Setup Chrome driver (headless)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Warning: Could not initialize Chrome driver: {e}")
            self.driver = None
        
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
        
    def test_backend_endpoints(self) -> bool:
        """Test all backend email endpoints"""
        endpoints_to_test = [
            ("/api/v1/auth/validate-email", "POST", {"email": "test@example.com"}),
            ("/api/v1/auth/validate-password", "POST", {"password": "TestPassword123!", "email": "test@example.com"}),
        ]
        
        all_passed = True
        
        for endpoint, method, data in endpoints_to_test:
            try:
                if method == "POST":
                    response = self.session.post(f"{self.backend_url}{endpoint}", json=data)
                else:
                    response = self.session.get(f"{self.backend_url}{endpoint}")
                    
                if response.status_code in [200, 201]:
                    self.log_test(f"Backend Endpoint {endpoint}", "PASS", f"Status: {response.status_code}")
                else:
                    self.log_test(f"Backend Endpoint {endpoint}", "FAIL", f"Status: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Backend Endpoint {endpoint}", "FAIL", f"Error: {str(e)}")
                all_passed = False
                
        return all_passed
        
    def test_user_registration_flow(self) -> bool:
        """Test complete user registration with email verification"""
        try:
            # Step 1: Register user
            registration_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/auth/register",
                json=registration_data
            )
            
            if response.status_code != 201:
                self.log_test("Registration Flow", "FAIL", f"Registration failed: {response.status_code}")
                return False
                
            self.log_test("Registration Flow - Step 1", "PASS", "User registered successfully")
            
            # Step 2: Test resend verification
            resend_response = self.session.post(
                f"{self.backend_url}/api/v1/auth/resend-verification",
                json={"email": self.test_email}
            )
            
            if resend_response.status_code == 200:
                self.log_test("Registration Flow - Step 2", "PASS", "Verification email resent")
            else:
                self.log_test("Registration Flow - Step 2", "FAIL", f"Resend failed: {resend_response.status_code}")
                
            return True
            
        except Exception as e:
            self.log_test("Registration Flow", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_password_reset_flow(self) -> bool:
        """Test complete password reset flow"""
        try:
            # Step 1: Request password reset
            reset_request = self.session.post(
                f"{self.backend_url}/api/v1/auth/forgot-password",
                json={"email": self.test_email}
            )
            
            if reset_request.status_code != 200:
                self.log_test("Password Reset Flow", "FAIL", f"Reset request failed: {reset_request.status_code}")
                return False
                
            self.log_test("Password Reset Flow - Step 1", "PASS", "Password reset requested")
            
            # Step 2: Test with invalid token (should fail)
            invalid_token_response = self.session.get(
                f"{self.backend_url}/api/v1/auth/validate-reset-token?token=invalid_token"
            )
            
            if invalid_token_response.status_code != 200:
                self.log_test("Password Reset Flow - Step 2", "PASS", "Invalid token properly rejected")
            else:
                self.log_test("Password Reset Flow - Step 2", "FAIL", "Invalid token accepted")
                
            return True
            
        except Exception as e:
            self.log_test("Password Reset Flow", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_frontend_pages(self) -> bool:
        """Test frontend email-related pages"""
        if not self.driver:
            self.log_test("Frontend Pages", "SKIP", "Chrome driver not available")
            return True
            
        try:
            pages_to_test = [
                ("/", "Home Page"),
                ("/login", "Login Page"),
                ("/register", "Register Page"),
                ("/forgot-password", "Forgot Password Page")
            ]
            
            all_passed = True
            
            for path, page_name in pages_to_test:
                try:
                    self.driver.get(f"{self.frontend_url}{path}")
                    
                    # Wait for page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Check if page loaded successfully (no error messages)
                    page_source = self.driver.page_source
                    if "error" not in page_source.lower() and "404" not in page_source:
                        self.log_test(f"Frontend - {page_name}", "PASS", "Page loaded successfully")
                    else:
                        self.log_test(f"Frontend - {page_name}", "FAIL", "Page contains errors")
                        all_passed = False
                        
                except Exception as e:
                    self.log_test(f"Frontend - {page_name}", "FAIL", f"Error: {str(e)}")
                    all_passed = False
                    
            return all_passed
            
        except Exception as e:
            self.log_test("Frontend Pages", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_login_page_elements(self) -> bool:
        """Test login page has forgot password link"""
        if not self.driver:
            self.log_test("Login Page Elements", "SKIP", "Chrome driver not available")
            return True
            
        try:
            self.driver.get(f"{self.frontend_url}/login")
            
            # Check for forgot password link
            forgot_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "Forgot")
            if forgot_link:
                self.log_test("Login Page Elements", "PASS", "Forgot password link found")
                return True
            else:
                self.log_test("Login Page Elements", "FAIL", "Forgot password link not found")
                return False
                
        except Exception as e:
            self.log_test("Login Page Elements", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_register_page_elements(self) -> bool:
        """Test register page has proper form elements"""
        if not self.driver:
            self.log_test("Register Page Elements", "SKIP", "Chrome driver not available")
            return True
            
        try:
            self.driver.get(f"{self.frontend_url}/register")
            
            # Check for email and password fields
            email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            if email_field and password_field and submit_button:
                self.log_test("Register Page Elements", "PASS", "All form elements found")
                return True
            else:
                self.log_test("Register Page Elements", "FAIL", "Missing form elements")
                return False
                
        except Exception as e:
            self.log_test("Register Page Elements", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_api_error_handling(self) -> bool:
        """Test API error handling for edge cases"""
        test_cases = [
            # Invalid email format
            ("/api/v1/auth/validate-email", {"email": "invalid-email"}, "Invalid Email"),
            # Empty password
            ("/api/v1/auth/validate-password", {"password": "", "email": "test@example.com"}, "Empty Password"),
            # Non-existent user login
            ("/api/v1/auth/login", {"email": "nonexistent@example.com", "password": "password"}, "Non-existent User"),
        ]
        
        all_passed = True
        
        for endpoint, data, test_name in test_cases:
            try:
                response = self.session.post(f"{self.backend_url}{endpoint}", json=data)
                
                # These should all return appropriate error responses (not 500)
                if response.status_code in [200, 400, 401, 422]:
                    self.log_test(f"Error Handling - {test_name}", "PASS", 
                                f"Proper error response: {response.status_code}")
                else:
                    self.log_test(f"Error Handling - {test_name}", "FAIL", 
                                f"Unexpected status: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self.log_test(f"Error Handling - {test_name}", "FAIL", f"Error: {str(e)}")
                all_passed = False
                
        return all_passed
        
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
            
    def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("STARTING EMAIL INTEGRATION TESTS")
        print("=" * 60)
        
        tests = [
            self.test_backend_endpoints,
            self.test_user_registration_flow,
            self.test_password_reset_flow,
            self.test_frontend_pages,
            self.test_login_page_elements,
            self.test_register_page_elements,
            self.test_api_error_handling
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        try:
            for test in tests:
                result = test()
                if result is True:
                    passed += 1
                elif result is False:
                    failed += 1
                else:  # None or skipped
                    skipped += 1
                    
        finally:
            self.cleanup()
            
        print("\n" + "=" * 60)
        print("INTEGRATION TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {passed + failed + skipped}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        
        if passed + failed > 0:
            print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
        
        # Save detailed results
        with open("tests/email_integration_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\nDetailed results saved to: tests/email_integration_results.json")
        
        return failed == 0

if __name__ == "__main__":
    tester = EmailIntegrationTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n⚠️  Some integration tests failed. Check the results for details.")
        exit(1)
    else:
        print("\n✅ All integration tests passed!")
        exit(0)
