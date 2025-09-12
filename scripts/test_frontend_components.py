#!/usr/bin/env python3
"""
Frontend Component Testing Script

This script tests the frontend React components for email functionality
by checking if components exist, have proper structure, and integration points.

Usage: python scripts/test_frontend_components.py
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any

class FrontendComponentTester:
    def __init__(self, frontend_path: str = "frontend/src"):
        self.frontend_path = Path(frontend_path)
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
    def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        full_path = self.frontend_path / file_path
        return full_path.exists()
        
    def read_file_content(self, file_path: str) -> str:
        """Read file content"""
        try:
            full_path = self.frontend_path / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return ""
            
    def check_component_structure(self, file_path: str, required_elements: List[str]) -> bool:
        """Check if component has required elements"""
        content = self.read_file_content(file_path)
        if not content:
            return False
            
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
                
        if missing_elements:
            self.log_test(f"Component Structure - {file_path}", "FAIL", 
                         f"Missing: {', '.join(missing_elements)}")
            return False
        else:
            self.log_test(f"Component Structure - {file_path}", "PASS", 
                         "All required elements present")
            return True
            
    def check_imports(self, file_path: str, required_imports: List[str]) -> bool:
        """Check if file has required imports"""
        content = self.read_file_content(file_path)
        if not content:
            return False
            
        missing_imports = []
        for import_stmt in required_imports:
            if import_stmt not in content:
                missing_imports.append(import_stmt)
                
        if missing_imports:
            self.log_test(f"Imports - {file_path}", "FAIL", 
                         f"Missing: {', '.join(missing_imports)}")
            return False
        else:
            self.log_test(f"Imports - {file_path}", "PASS", "All required imports present")
            return True
            
    def test_email_service(self) -> bool:
        """Test email service file"""
        file_path = "services/emailService.js"
        
        if not self.check_file_exists(file_path):
            self.log_test("Email Service", "FAIL", "File does not exist")
            return False
            
        required_methods = [
            "verifyEmail",
            "resendVerificationEmail", 
            "requestPasswordReset",
            "validateResetToken",
            "resetPassword"
        ]
        
        return self.check_component_structure(file_path, required_methods)
        
    def test_api_service(self) -> bool:
        """Test API service file"""
        file_path = "services/api.js"
        
        if not self.check_file_exists(file_path):
            self.log_test("API Service", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "axios",
            "apiClient",
            "interceptors",
            "Authorization"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_verify_email_page(self) -> bool:
        """Test VerifyEmailPage component"""
        file_path = "pages/VerifyEmailPage.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("VerifyEmailPage", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "useParams",
            "useNavigate",
            "verifyEmail",
            "token",
            "verificationStatus"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_forgot_password_page(self) -> bool:
        """Test ForgotPasswordPage component"""
        file_path = "pages/ForgotPasswordPage.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("ForgotPasswordPage", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "emailService",
            "requestPasswordReset",
            "email",
            "isLoading",
            "isEmailSent"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_reset_password_page(self) -> bool:
        """Test ResetPasswordPage component"""
        file_path = "pages/ResetPasswordPage.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("ResetPasswordPage", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "useParams",
            "token",
            "password",
            "confirmPassword",
            "validateResetToken",
            "resetPassword"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_email_verification_status(self) -> bool:
        """Test EmailVerificationStatus component"""
        file_path = "components/auth/EmailVerificationStatus.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("EmailVerificationStatus", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "resendVerification",
            "isResending",
            "email_verified",
            "handleResendVerification"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_notification_context(self) -> bool:
        """Test NotificationContext"""
        file_path = "contexts/NotificationContext.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("NotificationContext", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "createContext",
            "useNotifications",
            "NotificationProvider",
            "addNotification",
            "markAsRead"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_notification_center(self) -> bool:
        """Test NotificationCenter component"""
        file_path = "components/common/NotificationCenter.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("NotificationCenter", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "useNotifications",
            "notifications",
            "unreadCount",
            "markAsRead",
            "isOpen"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_app_routes(self) -> bool:
        """Test AppRoutes configuration"""
        file_path = "components/common/AppRoutes.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("AppRoutes", "FAIL", "File does not exist")
            return False
            
        required_routes = [
            "/verify-email/:token",
            "/forgot-password",
            "/reset-password/:token",
            "VerifyEmailPage",
            "ForgotPasswordPage",
            "ResetPasswordPage"
        ]
        
        return self.check_component_structure(file_path, required_routes)
        
    def test_login_page_integration(self) -> bool:
        """Test LoginPage has forgot password link"""
        file_path = "pages/LoginPage.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("LoginPage Integration", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "/forgot-password",
            "Forgot your password"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def test_app_integration(self) -> bool:
        """Test App.jsx has all providers"""
        file_path = "App.jsx"
        
        if not self.check_file_exists(file_path):
            self.log_test("App Integration", "FAIL", "File does not exist")
            return False
            
        required_elements = [
            "AuthProvider",
            "NotificationProvider", 
            "Toaster",
            "AppRoutes"
        ]
        
        return self.check_component_structure(file_path, required_elements)
        
    def check_environment_setup(self) -> bool:
        """Check environment configuration"""
        env_files = [".env", ".env.local", ".env.development"]
        
        for env_file in env_files:
            if self.check_file_exists(f"../{env_file}"):
                content = self.read_file_content(f"../{env_file}")
                if "VITE_API_BASE_URL" in content:
                    self.log_test("Environment Setup", "PASS", f"Found config in {env_file}")
                    return True
                    
        self.log_test("Environment Setup", "FAIL", "No VITE_API_BASE_URL found")
        return False
        
    def run_all_tests(self):
        """Run all frontend component tests"""
        print("=" * 60)
        print("STARTING FRONTEND COMPONENT TESTS")
        print("=" * 60)
        
        tests = [
            self.test_email_service,
            self.test_api_service,
            self.test_verify_email_page,
            self.test_forgot_password_page,
            self.test_reset_password_page,
            self.test_email_verification_status,
            self.test_notification_context,
            self.test_notification_center,
            self.test_app_routes,
            self.test_login_page_integration,
            self.test_app_integration,
            self.check_environment_setup
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
                
        print("\n" + "=" * 60)
        print("FRONTEND COMPONENT TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
        
        # Save detailed results
        os.makedirs("scripts/test_results", exist_ok=True)
        with open("scripts/test_results/frontend_component_tests.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\nDetailed results saved to: scripts/test_results/frontend_component_tests.json")
        
        return failed == 0

if __name__ == "__main__":
    tester = FrontendComponentTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n⚠️  Some component tests failed. Check the results for details.")
        exit(1)
    else:
        print("\n✅ All component tests passed!")
        exit(0)
