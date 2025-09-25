"""
AI Service Implementation

This module provides the main AI service that coordinates different AI providers.
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from datetime import datetime
import traceback

from ...domain.ai.interfaces import (
    AIServiceInterface, AIProviderInterface, AIRequest, AIResponse, 
    StreamChunk, AIMessage, MessageRole
)
from ...infrastructure.ai.config import AIProvider, AIModel, ai_settings

# Protected imports for providers
try:
    from ...infrastructure.ai.providers.anthropic_provider import AnthropicProvider
except ImportError:
    AnthropicProvider = None

try:
    from ...infrastructure.ai.providers.gemini_provider import GeminiProvider
except ImportError:
    GeminiProvider = None


class AIService(AIServiceInterface):
    """Main AI service implementation."""
    
    def __init__(self):
        """Initialize the AI service with available providers."""
        self._providers: Dict[AIProvider, AIProviderInterface] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available AI providers."""
        
        # Initialize Anthropic provider
        if AnthropicProvider and ai_settings.anthropic_api_key:
            try:
                self._providers[AIProvider.ANTHROPIC] = AnthropicProvider()
            except Exception as e:
                print(f"Failed to initialize Anthropic provider: {e}")
        
        # Initialize Google Gemini provider  
        if GeminiProvider and ai_settings.google_api_key:
            try:
                self._providers[AIProvider.GOOGLE] = GeminiProvider()
            except Exception as e:
                print(f"Failed to initialize Gemini provider: {e}")
        
        print(f"Initialized providers: {list(self._providers.keys())}")
    
    def _get_provider_for_model_internal(self, model: AIModel) -> Optional[AIProviderInterface]:
        """Get the appropriate provider for a given model."""
        
        # Gemini models
        if model.value.startswith('gemini'):
            return self._providers.get(AIProvider.GOOGLE)
        
        # Claude models
        if model.value.startswith('claude'):
            return self._providers.get(AIProvider.ANTHROPIC)
            
        # Default fallback
        if self._providers:
            return list(self._providers.values())[0]
        
        return None
    

    
    # Interface implementation
    async def generate_response(
        self,
        messages: List[AIMessage],
        model: Optional[AIModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Generate a single AI response."""
        
        # Use default model if not specified
        if not model:
            # Use Claude as fallback if Gemini not available
            if AIProvider.GOOGLE in self._providers:
                model = AIModel.GEMINI_2_0_FLASH
            else:
                model = AIModel.CLAUDE_3_HAIKU  # Fallback to Claude Haiku
        
        # Find appropriate provider
        provider_impl = self._get_provider_for_model_internal(model)
        
        if not provider_impl:
            raise ValueError(f"No available provider supports model {model.value}")
        
        # Create AI request
        request = AIRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            functions=metadata.get("functions") if metadata else None
        )
        
        # Generate response
        start_time = datetime.utcnow()
        response = await provider_impl.generate_response(request)
        end_time = datetime.utcnow()
        
        # Add processing time
        response.processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return response
    
    async def generate_streaming_response(  # type: ignore
        self,
        messages: List[AIMessage],
        model: Optional[AIModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming AI response."""
        
        # Use default model if not specified
        if not model:
            # Use Claude as fallback if Gemini not available
            if AIProvider.GOOGLE in self._providers:
                model = AIModel.GEMINI_2_0_FLASH
            else:
                model = AIModel.CLAUDE_3_HAIKU  # Fallback to Claude Haiku
        
        # Find appropriate provider
        provider_impl = self._get_provider_for_model_internal(model)
        
        if not provider_impl:
            raise ValueError(f"No available provider supports model {model.value}")
        
        # Create AI request
        request = AIRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            functions=metadata.get("functions") if metadata else None
        )
        
        # Generate streaming response
        stream = provider_impl.generate_streaming_response(request)  # type: ignore
        async for chunk in stream:  # type: ignore
            yield chunk
    
    # Service management methods
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [provider.value for provider in self._providers.keys()]
    
    def get_available_models(self) -> List[AIModel]:
        """Get list of available models from all providers."""
        models = []
        for provider in self._providers.values():
            try:
                provider_models = provider.get_supported_models()
                for model_name in provider_models:
                    try:
                        models.append(AIModel(model_name))
                    except ValueError:
                        # Skip invalid model names
                        pass
            except Exception:
                # Skip providers that fail
                pass
        return models
    
    def is_provider_available(self, provider: AIProvider) -> bool:
        """Check if a specific provider is available."""
        return provider in self._providers
    
    def get_default_model(self) -> AIModel:
        """Get the default model."""
        return AIModel(ai_settings.default_model)
    
    def get_streaming_enabled(self) -> bool:
        """Check if streaming is enabled."""
        return ai_settings.enable_streaming
    
    async def get_conversation_summary(
        self,
        messages: List[AIMessage],
        max_length: int = 200
    ) -> str:
        """Generate a summary of the conversation."""
        # Simple implementation - just return the last few messages
        if not messages:
            return "Empty conversation"
        
        # Get last few messages for summary
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        summary_parts = []
        
        for msg in recent_messages:
            role = msg.role.value.capitalize()
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{role}: {content}")
        
        full_summary = " | ".join(summary_parts)
        if len(full_summary) > max_length:
            full_summary = full_summary[:max_length-3] + "..."
        
        return full_summary
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        # Simple sentiment analysis implementation
        # In a real implementation, you would use the AI providers
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'horrible', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = "negative"  
            confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_score": positive_count,
            "negative_score": negative_count
        }
    
    def get_provider_for_model(self, model: AIModel) -> AIProvider:
        """Get the provider for a specific model."""
        # Gemini models
        if model.value.startswith('gemini'):
            return AIProvider.GOOGLE
        
        # Claude models
        if model.value.startswith('claude'):
            return AIProvider.ANTHROPIC
            
        # Default fallback
        if self._providers:
            return list(self._providers.keys())[0]
        
        raise ValueError(f"No provider available for model {model.value}")
    
    # Additional service methods needed by other components
    def get_service_status(self) -> Dict[str, Any]:
        """Get the current service status."""
        return {
            "available_providers": self.get_available_providers(),
            "default_model": ai_settings.default_model,
            "streaming_enabled": ai_settings.enable_streaming,
            "status": "active" if self._providers else "inactive"
        }
    
    async def generate_chat_response(
        self, 
        messages: List[AIMessage],
        model_name: Optional[str] = None
    ) -> AIResponse:
        """Generate response for chat service."""
        model = None
        if model_name:
            try:
                model = AIModel(model_name)
            except ValueError:
                model = None
        
        return await self.generate_response(messages, model=model)
    
    async def generate_chat_streaming_response(
        self, 
        messages: List[AIMessage],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate streaming response for chat service."""
        model = None
        if model_name:
            try:
                model = AIModel(model_name)
            except ValueError:
                model = None
        
        async for chunk in self.generate_streaming_response(messages, model=model):
            yield chunk
    
    def _convert_chat_messages_to_ai_messages(self, messages: List[Dict[str, Any]]) -> List[AIMessage]:
        """Convert chat messages to AI messages."""
        ai_messages = []
        
        for msg in messages:
            role_str = msg.get('role', 'user')
            if role_str == 'user':
                role = MessageRole.USER
            elif role_str == 'assistant':
                role = MessageRole.ASSISTANT
            else:
                role = MessageRole.SYSTEM
                
            ai_messages.append(AIMessage(
                role=role,
                content=msg.get('content', ''),
                metadata=msg.get('metadata'),
                function_call=msg.get('function_call')
            ))
        
        return ai_messages


# Global service instance
ai_service = AIService()