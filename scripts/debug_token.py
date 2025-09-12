#!/usr/bin/env python3
"""
Debug token verification
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
test_email = f"debug_token_{int(datetime.now().timestamp())}@example.com"
test_password = "TestPassword123!"

def debug_token():
    """Debug token creation and verification"""
    session = requests.Session()
    
    print("🔍 Debug Token Verification")
    print("=" * 40)
    
    # Register and login
    print("1️⃣ Registering user...")
    register_response = session.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": test_password
    })
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return
    
    print("2️⃣ Logging in...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = login_response.json()
    print(f"📋 Full login response:")
    print(json.dumps(login_data, indent=2, default=str))
    
    tokens = login_data.get("tokens", {})
    access_token = tokens.get("access_token")
    
    if not access_token:
        print("❌ No access token in response")
        return
    
    print(f"\n🔑 Access token: {access_token}")
    
    # Try to decode the token manually using Python
    try:
        import jwt
        import base64
        
        # Decode without verification to see payload
        payload = jwt.decode(access_token, options={"verify_signature": False})
        print(f"\n📋 Token payload:")
        print(json.dumps(payload, indent=2, default=str))
        
        user_id = payload.get("sub")
        print(f"\n🆔 User ID from token: {user_id}")
        print(f"🔍 User ID type: {type(user_id)}")
        
        # Try to convert to UUID
        import uuid
        try:
            user_uuid = uuid.UUID(user_id)
            print(f"✅ UUID conversion successful: {user_uuid}")
        except ValueError as e:
            print(f"❌ UUID conversion failed: {e}")
            
    except Exception as e:
        print(f"❌ Token decode error: {e}")

if __name__ == "__main__":
    debug_token()
