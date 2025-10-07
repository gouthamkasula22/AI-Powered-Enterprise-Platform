"""
Quick test script to upload an Excel file via the correct endpoint.
"""
import requests
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
EXCEL_FILE = input("Enter path to your Excel file: ").strip().strip('"')

# Check file exists
if not Path(EXCEL_FILE).exists():
    print(f"[ERROR] File not found: {EXCEL_FILE}")
    sys.exit(1)

print(f"[OK] Found file: {EXCEL_FILE}")

# Step 1: Login
print("\n" + "="*60)
print("Step 1: Logging in...")
print("="*60)

login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "testuser@example.com",
        "password": "TestPass123!"
    }
)

if login_response.status_code != 200:
    print(f"[ERROR] Login failed: {login_response.status_code}")
    print(login_response.json())
    sys.exit(1)

token = login_response.json()["access_token"]
print(f"[OK] Logged in successfully")

# Step 2: Upload Excel file
print("\n" + "="*60)
print("Step 2: Uploading Excel file...")
print("="*60)

headers = {"Authorization": f"Bearer {token}"}

with open(EXCEL_FILE, "rb") as f:
    files = {"file": (Path(EXCEL_FILE).name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    
    # Use the CORRECT endpoint for Excel
    upload_response = requests.post(
        f"{BASE_URL}/api/v1/excel/upload",  # ← CORRECT endpoint
        headers=headers,
        files=files
    )

print(f"Response Status: {upload_response.status_code}")

if upload_response.status_code == 201:
    result = upload_response.json()
    print(f"[OK] SUCCESS! Excel uploaded successfully")
    print(f"\nDocument ID: {result['id']}")
    print(f"Filename: {result['filename']}")
    print(f"Status: {result['status']}")
    print(f"Sheets: {result['sheet_count']}")
    print(f"Total Rows: {result['total_rows']}")
    print(f"Total Columns: {result['total_columns']}")
    
    # Wait a moment for processing
    import time
    if result['status'] == 'processing':
        print("\n[INFO] Document is processing, waiting...")
        time.sleep(2)
        
        # Check status
        status_response = requests.get(
            f"{BASE_URL}/api/v1/excel/{result['id']}",
            headers=headers
        )
        if status_response.status_code == 200:
            updated = status_response.json()
            print(f"[OK] Processing complete! Status: {updated['status']}")
else:
    print(f"[ERROR] Upload failed")
    print(f"Response: {upload_response.text}")
