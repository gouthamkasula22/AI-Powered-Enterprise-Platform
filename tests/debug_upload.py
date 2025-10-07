"""
Debug Excel Upload - Check backend error details
"""
import requests
import sys
from pathlib import Path

# Load env
backend_env_path = Path(__file__).parent.parent / "backend" / ".env"
if backend_env_path.exists():
    import os
    with open(backend_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

BASE_URL = "http://localhost:8000"
AUTH_BASE = f"{BASE_URL}/api/auth"
API_BASE = f"{BASE_URL}/api/v1"

# Login
print("Logging in...")
response = requests.post(
    f"{AUTH_BASE}/login",
    json={"email": "testuser@example.com", "password": "TestPass123!"}
)
if response.status_code != 200:
    print(f"Login failed: {response.status_code} - {response.text}")
    sys.exit(1)

token = response.json()["access_token"]
print(f"Logged in successfully")

# Create test file
print("\nCreating test file...")
import pandas as pd
test_file = Path(__file__).parent / "debug_test.xlsx"
df = pd.DataFrame({
    'Product': ['Laptop', 'Mouse'],
    'Price': [999, 25]
})
df.to_excel(test_file, index=False)
print(f"Test file created: {test_file}")

# Try upload with detailed error handling
print("\nAttempting upload...")
headers = {"Authorization": f"Bearer {token}"}

try:
    with open(test_file, 'rb') as f:
        files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(
            f"{API_BASE}/excel/upload",
            headers=headers,
            files=files,
            timeout=30
        )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code in [200, 201]:
        print("\n✓ Upload successful!")
        print(f"Document: {response.json()}")
    else:
        print(f"\n✗ Upload failed")
        
except Exception as e:
    print(f"\nException occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print(f"\nCleaned up test file")
