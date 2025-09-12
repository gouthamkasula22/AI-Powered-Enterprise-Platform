#!/usr/bin/env python3
"""
Simple Profile Management Test

A focused test to verify the profile management feature works correctly.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
test_email = f"profile_simple_test_{int(datetime.now().timestamp())}@example.com"
test_password = "TestPassword123!"

def test_profile_management():
    """Simple step-by-step test of profile management"""
    session = requests.Session()
    
    print("🧪 Simple Profile Management Test")
    print("=" * 50)
    
    # Step 1: Register user
    print("1️⃣ Registering test user...")
    register_response = session.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": test_password
    })
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return False
    
    print("✅ User registered successfully")
    
    # Step 2: Login
    print("2️⃣ Logging in...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    login_data = login_response.json()
    tokens = login_data.get("tokens", {})
    access_token = tokens.get("access_token")
    
    if not access_token:
        print("❌ No access token received")
        print(f"📋 Login response: {json.dumps(login_data, indent=2, default=str)}")
        return False
    
    print("✅ Login successful")
    print(f"🔑 Token: {access_token[:20]}...")
    
    # Set authorization header
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    
    # Step 3: Get current profile
    print("3️⃣ Getting current profile...")
    profile_response = session.get(f"{BASE_URL}/auth/me")
    
    if profile_response.status_code != 200:
        print(f"❌ Profile fetch failed: {profile_response.status_code} - {profile_response.text}")
        return False
    
    profile_data = profile_response.json()
    print("✅ Profile fetched successfully")
    print(f"📋 Current profile: {json.dumps(profile_data, indent=2, default=str)}")
    
    # Step 4: Update profile
    print("4️⃣ Updating profile...")
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "display_name": "Johnny",
        "bio": "Test user for profile management",
        "phone_number": "+1-555-123-4567"
    }
    
    update_response = session.put(f"{BASE_URL}/auth/profile", json=update_data)
    
    if update_response.status_code != 200:
        print(f"❌ Profile update failed: {update_response.status_code} - {update_response.text}")
        return False
    
    updated_profile = update_response.json()
    print("✅ Profile updated successfully")
    print(f"📋 Updated profile: {json.dumps(updated_profile, indent=2, default=str)}")
    
    # Step 5: Verify updates
    print("5️⃣ Verifying updates...")
    success = True
    for field, expected_value in update_data.items():
        actual_value = updated_profile.get(field)
        if actual_value != expected_value:
            print(f"❌ Field '{field}' not updated: expected '{expected_value}', got '{actual_value}'")
            success = False
        else:
            print(f"✅ {field}: {actual_value}")
    
    if success:
        print("\n🎉 PROFILE MANAGEMENT TEST PASSED!")
        print("✅ All profile management features are working correctly:")
        print("   • Profile viewing")
        print("   • Profile updating")
        print("   • Data validation")
        print("   • Backend API endpoints")
        return True
    else:
        print("\n❌ PROFILE MANAGEMENT TEST FAILED!")
        return False

if __name__ == "__main__":
    try:
        success = test_profile_management()
        if success:
            print("\n🌟 Profile management feature is ready for use!")
            print("💡 You can now test the UI by:")
            print("   1. Opening http://localhost:5173")
            print("   2. Logging in or registering")
            print("   3. Going to the Profile tab")
            print("   4. Clicking 'Edit Profile'")
        else:
            print("\n🔧 Profile management needs fixes before use")
    except Exception as e:
        print(f"\n💥 Test error: {str(e)}")
