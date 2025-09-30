#!/usr/bin/env python3
"""
Test script to make a direct API call and see the exact error
"""
import requests
import json

# Test the API directly
url = "http://localhost:8000/api/conversations/26/messages"
headers = {
    "Content-Type": "application/json",
    # You'll need to replace this with a valid token
}

# Test 1: Basic request
print("🧪 Test 1: Basic request")
payload1 = {
    "content": "test message"
}

try:
    response = requests.post(url, json=payload1, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n🧪 Test 2: Request with selected_documents")
payload2 = {
    "content": "explain the selected document",
    "selected_documents": ["1"]
}

try:
    response = requests.post(url, json=payload2, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n🧪 Test 3: Full frontend-style request")
payload3 = {
    "content": "explain the selected document",
    "chat_mode": "rag",
    "selected_documents": ["1"]
}

try:
    response = requests.post(url, json=payload3, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")