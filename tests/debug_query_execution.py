"""
Debug script to test query execution and see exact errors
"""
import requests
import pandas as pd
import json

API_BASE = "http://localhost:8000/api/v1"

# 1. Login
print("Logging in...")
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "testuser@example.com", "password": "TestPass123!"}
)
if response.status_code != 200:
    print(f"Login failed: {response.status_code} - {response.text}")
    exit(1)
token_data = response.json()
token = token_data.get("access_token") or token_data.get("token")
print(f"[OK] Logged in\n")

# 2. Create and upload test file
print("Creating test file...")
df = pd.DataFrame({
    "Product": ["Laptop", "Mouse"],
    "Quantity": [10, 50],
    "Price": [999.99, 29.99]
})
df.to_excel("debug_test.xlsx", index=False)
print("[OK] Test file created\n")

print("Uploading...")
with open("debug_test.xlsx", "rb") as f:
    response = requests.post(
        f"{API_BASE}/excel/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f}
    )
doc_id = response.json()["id"]
print(f"[OK] Uploaded (ID: {doc_id})\n")

# 3. Submit query
print("Submitting query...")
response = requests.post(
    f"{API_BASE}/excel/{doc_id}/query",
    headers={"Authorization": f"Bearer {token}"},
    json={"query_text": "What is the total quantity?", "target_sheet": "Sheet1"}
)
print(f"Response status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")
query_id = response.json()["id"]
print(f"[OK] Query submitted (ID: {query_id})\n")

# 4. Execute query - THIS IS WHERE THE ERROR HAPPENS
print("="*60)
print("EXECUTING QUERY - Watch backend logs for detailed traceback")
print("="*60)
response = requests.post(
    f"{API_BASE}/excel/{doc_id}/queries/{query_id}/execute",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"\nResponse status: {response.status_code}")
if response.status_code == 200:
    print("[OK] SUCCESS!")
    print(json.dumps(response.json(), indent=2))
else:
    print("[ERROR]")
    print(f"Error: {response.json().get('detail', response.text)}")

# Cleanup
import os
os.remove("debug_test.xlsx")
