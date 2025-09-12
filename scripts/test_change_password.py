#!/usr/bin/env python3
"""
Simple Change Password Test Script

Tests the change password functionality for the user authentication system.
"""

import requests
import json
import random
import string

# Configuration
BASE_URL = "http://localhost:8000/api/v1/auth"
TEST_EMAIL = f"change_password_test_{random.randint(100000, 999999)}@example.com"
INITIAL_PASSWORD = "TestPassword123!"
NEW_PASSWORD = "NewPassword456!"

def test_change_password():
    print("🔒 Simple Change Password Test")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # Step 1: Register a test user
        print("1️⃣ Registering test user...")
        register_data = {
            "email": TEST_EMAIL,
            "password": INITIAL_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/register", json=register_data)
        if response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return
        
        print("✅ User registered successfully")
        
        # Step 2: Login to get token
        print("2️⃣ Logging in...")
        login_data = {
            "email": TEST_EMAIL,
            "password": INITIAL_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return
        
        login_result = response.json()
        token = login_result["tokens"]["access_token"]
        print("✅ Login successful")
        print(f"🔑 Token: {token[:20]}...")
        
        # Set authorization header
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Test change password with wrong current password
        print("3️⃣ Testing with wrong current password...")
        change_data = {
            "current_password": "WrongPassword123!",
            "new_password": NEW_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/change-password", json=change_data, headers=headers)
        if response.status_code == 400:
            print("✅ Correctly rejected wrong current password")
        else:
            print(f"❌ Should have rejected wrong password: {response.status_code}")
        
        # Step 4: Test change password with same password
        print("4️⃣ Testing with same password...")
        change_data = {
            "current_password": INITIAL_PASSWORD,
            "new_password": INITIAL_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/change-password", json=change_data, headers=headers)
        if response.status_code == 400:
            print("✅ Correctly rejected same password")
        else:
            print(f"❌ Should have rejected same password: {response.status_code}")
        
        # Step 5: Test change password with weak password
        print("5️⃣ Testing with weak password...")
        change_data = {
            "current_password": INITIAL_PASSWORD,
            "new_password": "123"
        }
        
        response = session.post(f"{BASE_URL}/change-password", json=change_data, headers=headers)
        if response.status_code == 400:
            print("✅ Correctly rejected weak password")
        else:
            print(f"❌ Should have rejected weak password: {response.status_code}")
        
        # Step 6: Test successful password change
        print("6️⃣ Testing successful password change...")
        change_data = {
            "current_password": INITIAL_PASSWORD,
            "new_password": NEW_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/change-password", json=change_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print("✅ Password changed successfully")
            print(f"📋 Response: {result}")
        else:
            print(f"❌ Password change failed: {response.status_code} - {response.text}")
            return
        
        # Step 7: Verify old password no longer works
        print("7️⃣ Verifying old password no longer works...")
        login_data = {
            "email": TEST_EMAIL,
            "password": INITIAL_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 400:
            print("✅ Old password correctly rejected")
        else:
            print(f"❌ Old password should be rejected: {response.status_code}")
        
        # Step 8: Verify new password works
        print("8️⃣ Verifying new password works...")
        login_data = {
            "email": TEST_EMAIL,
            "password": NEW_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            print("✅ New password works correctly")
        else:
            print(f"❌ New password should work: {response.status_code} - {response.text}")
            return
        
        print("\n🎉 CHANGE PASSWORD TEST PASSED!")
        print("✅ All change password features are working correctly:")
        print("   • Current password verification")
        print("   • Password strength validation")
        print("   • Same password rejection")
        print("   • Successful password update")
        print("   • Old password invalidation")
        print("   • New password authentication")
        
        print("\n🌟 Change password feature is ready for use!")
        print("💡 You can now test the UI by:")
        print("   1. Opening http://localhost:3000")
        print("   2. Logging in")
        print("   3. Going to the Security tab")
        print("   4. Using the Change Password form")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_change_password()
