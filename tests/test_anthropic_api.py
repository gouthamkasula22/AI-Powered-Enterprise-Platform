"""
Simple test to verify Anthropic API key and model access.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
env_path = backend_path / ".env"
load_dotenv(env_path)

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("[ERROR] ANTHROPIC_API_KEY not found in .env file")
    sys.exit(1)

print(f"[OK] API Key found (length: {len(api_key)})")
print(f"[OK] API Key starts with: {api_key[:10]}...")

# Try to create client
try:
    client = Anthropic(api_key=api_key)
    print("[OK] Anthropic client created")
except Exception as e:
    print(f"[ERROR] Failed to create client: {e}")
    sys.exit(1)

# Test different model names
models_to_test = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
]

print("\n" + "="*60)
print("Testing model access...")
print("="*60)

for model in models_to_test:
    print(f"\nTesting: {model}")
    try:
        from anthropic.types import TextBlock
        
        message = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'hello' in one word."
                }
            ]
        )
        # Extract text from TextBlock
        response = ""
        for block in message.content:
            if isinstance(block, TextBlock):
                response = block.text
                break
        print(f"  [OK] SUCCESS! Response: {response}")
        print(f"  [OK] This model works! Use: {model}")
        break  # Found a working model, stop testing
    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "not_found" in error_str:
            print(f"  [ERROR] Model not found (404)")
        elif "401" in error_str or "authentication" in error_str.lower():
            print(f"  [ERROR] Authentication failed - API key invalid")
            break
        else:
            print(f"  [ERROR] {error_str[:100]}")
