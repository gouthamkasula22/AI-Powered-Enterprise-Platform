#!/usr/bin/env python3
"""
AI Integration Test Script

This script tests the AI integration functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend" 
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# Load environment variables from backend/.env
try:
    from dotenv import load_dotenv
    env_path = backend_path / ".env"
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
    print("🔒 Security Notice: API keys are loaded but will not be displayed for security")
except ImportError:
    print("⚠️  python-dotenv not installed, environment variables may not be loaded")
except Exception as e:
    print(f"⚠️  Failed to load .env file: {e}")

async def test_ai_service():
    """Test the AI service directly."""
    try:
        # Import AI service
        from src.application.services.ai_service import ai_service
        from src.domain.ai.interfaces import AIMessage, MessageRole
        
        print("🤖 Testing AI Service Integration")
        print("=" * 50)
        
        # Test service status
        print("\n📊 Service Status:")
        status = ai_service.get_service_status()
        print(f"Available providers: {status.get('available_providers', [])}")
        print(f"Default model: {status.get('default_model', 'Not set')}")
        print(f"Streaming enabled: {status.get('streaming_enabled', False)}")
        
        # Test available models
        print("\n🔧 Available Models:")
        models = ai_service.get_available_models()
        for model in models:
            print(f"  - {model.value}")
        
        # Test simple AI response (if API key is available)
        if ai_service.get_available_providers():
            print("\n💬 Testing AI Response:")
            test_messages = [
                AIMessage(
                    role=MessageRole.USER,
                    content="Hello! Can you help me test this AI integration?"
                )
            ]
            
            try:
                response = await ai_service.generate_response(test_messages)
                print(f"✅ Response: {response.content[:100]}...")
                print(f"✅ Model: {response.model}")
                print(f"✅ Tokens: {response.tokens_used}")
                print(f"✅ Processing time: {response.processing_time_ms}ms")
            except Exception as e:
                print(f"❌ Response failed: {str(e)}")
                
            # Test streaming response
            print("\n🌊 Testing Streaming Response:")
            try:
                full_response = ""
                async for chunk in ai_service.generate_streaming_response(test_messages):
                    full_response += chunk.delta
                    if chunk.is_complete:
                        print(f"✅ Streaming complete: {full_response[:100]}...")
                        break
            except Exception as e:
                print(f"❌ Streaming failed: {str(e)}")
        else:
            print("\n⚠️  No AI providers available (check API keys)")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_chat_integration():
    """Test the enhanced chat service with AI integration."""
    try:
        print("\n\n💬 Testing Chat Service AI Integration")
        print("=" * 50)
        
        # This would require database setup, so just test imports for now
        from src.application.services.enhanced_chat_service import EnhancedChatService
        from src.infrastructure.ai.config import AIModel
        
        print("✅ Chat service imports working")
        print("✅ AI models available:")
        for model in AIModel:
            print(f"  - {model.value}")
            
    except Exception as e:
        print(f"❌ Chat integration test failed: {str(e)}")


def test_configuration():
    """Test AI configuration."""
    try:
        print("\n\n⚙️  Testing AI Configuration")
        print("=" * 50)
        
        from src.infrastructure.ai.config import ai_settings, AIProvider, AIModel
        
        print(f"Google API Key configured: {'Yes' if ai_settings.google_api_key else 'No'}")
        print(f"Anthropic API Key configured: {'Yes' if ai_settings.anthropic_api_key else 'No'}")
        print(f"Default model: {ai_settings.default_model}")
        print(f"Default temperature: {ai_settings.default_temperature}")
        print(f"Streaming enabled: {ai_settings.enable_streaming}")
        
        print("\n🏗️  Available Providers:")
        for provider in AIProvider:
            print(f"  - {provider.value}")
            
        print("\n🤖 Available Models:")
        for model in AIModel:
            print(f"  - {model.value}")
            
        print("✅ Configuration test passed")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")


async def main():
    """Run all tests."""
    print("🚀 AI Integration Test Suite")
    print("=" * 60)
    
    # Test configuration
    test_configuration()
    
    # Test AI service
    await test_ai_service()
    
    # Test chat integration
    await test_chat_integration()
    
    print("\n\n🎉 Test Suite Complete!")
    print("=" * 60)
    
    # Environment check
    print("\n📋 Environment Check:")
    google_key = os.getenv("GOOGLE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if google_key:
        print("✅ GOOGLE_API_KEY: [CONFIGURED]")
    else:
        print("⚠️  GOOGLE_API_KEY not found in environment")
        print("   Set it with: export GOOGLE_API_KEY=your_key_here")
    
    if anthropic_key:
        print("✅ ANTHROPIC_API_KEY: [CONFIGURED]")
    else:
        print("⚠️  ANTHROPIC_API_KEY not found in environment")
        print("   Set it with: export ANTHROPIC_API_KEY=your_key_here")
    
    print("\n💡 Next Steps:")
    print("1. Set up your Google/Gemini API key and Anthropic API key")
    print("2. Test the API endpoints with the development server")
    print("3. Try the new AI-powered chat endpoints:")
    print("   - POST /api/chat/threads/{id}/ai-response")
    print("   - POST /api/chat/threads/{id}/ai-stream")
    print("   - GET /api/chat/ai/status")


if __name__ == "__main__":
    asyncio.run(main())