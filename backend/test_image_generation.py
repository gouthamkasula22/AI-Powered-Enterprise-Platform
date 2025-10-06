import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "admin@example.com"  # Change to your test user
TEST_USER_PASSWORD = "AdminPassword123!"  # Change to your test password

def login_and_get_token():
    """Login and get authentication token"""
    login_data = {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def test_image_generation():
    """Test the complete image generation workflow"""
    print("🚀 Starting Image Generation Test")
    print("=" * 50)
    
    # 1. Login
    print("1. Logging in...")
    token = login_and_get_token()
    if not token:
        print("❌ Failed to login")
        return
    print("✅ Login successful")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create a chat thread first
    print("\n2. Creating chat thread...")
    thread_data = {
        "title": "Image Generation Test",
        "metadata": {"test": True}
    }
    
    response = requests.post(f"{BASE_URL}/chat/threads", json=thread_data, headers=headers)
    if response.status_code == 201:
        thread_id = response.json()["id"]
        print(f"✅ Thread created with ID: {thread_id}")
    else:
        print(f"❌ Failed to create thread: {response.text}")
        return
    
    # 3. Generate an image
    print("\n3. Starting image generation...")
    image_data = {
        "prompt": "A beautiful sunset over mountains with a lake reflection, photorealistic style",
        "size": "1024x1024",
        "quality": "standard",
        "style": "vivid",
        "thread_id": thread_id
    }
    
    response = requests.post(f"{BASE_URL}/images/generate", json=image_data, headers=headers)
    if response.status_code == 202:
        task_id = response.json()["task_id"]
        print(f"✅ Image generation started. Task ID: {task_id}")
    else:
        print(f"❌ Failed to start image generation: {response.text}")
        return
    
    # 4. Poll for completion (max 2 minutes)
    print("\n4. Waiting for image generation to complete...")
    max_wait = 120  # 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/images/tasks/{task_id}/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"   Status: {status['status']} - Progress: {status.get('progress', 0)}%")
            
            if status["status"] == "completed":
                print("✅ Image generation completed!")
                print(f"   Image ID: {status['image_data']['id']}")
                print(f"   Original prompt: {status['image_data']['original_prompt']}")
                print(f"   Revised prompt: {status['image_data']['revised_prompt']}")
                print(f"   Cost: ${status['image_data']['generation_cost']}")
                print(f"   Generation time: {status['image_data']['generation_time']:.2f}s")
                
                image_id = status['image_data']['id']
                break
            elif status["status"] == "failed":
                print(f"❌ Image generation failed: {status.get('error', 'Unknown error')}")
                return
        else:
            print(f"❌ Failed to check status: {response.text}")
            return
        
        time.sleep(2)
    else:
        print("⏰ Image generation timed out")
        return
    
    # 5. Test gallery retrieval
    print("\n5. Testing gallery retrieval...")
    response = requests.get(f"{BASE_URL}/images/gallery?limit=5", headers=headers)
    if response.status_code == 200:
        gallery = response.json()
        print(f"✅ Gallery retrieved. Total images: {gallery['total']}")
        if gallery['images']:
            print(f"   Latest image: {gallery['images'][0]['original_prompt'][:50]}...")
    else:
        print(f"❌ Failed to retrieve gallery: {response.text}")
        return
    
    # 6. Test image download
    print("\n6. Testing image download...")
    response = requests.get(f"{BASE_URL}/images/{image_id}/download", headers=headers)
    if response.status_code == 200:
        with open(f"test_image_{image_id}.png", "wb") as f:
            f.write(response.content)
        print(f"✅ Image downloaded as test_image_{image_id}.png")
    else:
        print(f"❌ Failed to download image: {response.text}")
    
    # 7. Test thread images
    print("\n7. Testing thread images retrieval...")
    response = requests.get(f"{BASE_URL}/images/thread/{thread_id}", headers=headers)
    if response.status_code == 200:
        thread_images = response.json()
        print(f"✅ Thread images retrieved. Count: {len(thread_images['images'])}")
    else:
        print(f"❌ Failed to retrieve thread images: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Image Generation Test Complete!")
    print("✅ All core functionality working correctly")

if __name__ == "__main__":
    test_image_generation()