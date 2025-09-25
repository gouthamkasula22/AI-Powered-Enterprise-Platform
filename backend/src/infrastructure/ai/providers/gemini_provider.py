"""
Google Gemini Provider Implementation

This module provides the Google Gemini integration for AI services.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncIterator, AsyncGenerator
import json
import google.generativeai as genai
from google.generativeai import types
from datetime import datetime

from ....domain.ai.interfaces import (
    AIProviderInterface, AIRequest, AIResponse, StreamChunk, 
    AIMessage, MessageRole
)
from ..config import AIProvider, AIModel, ai_settings, get_model_config


class GeminiProvider(AIProviderInterface):
    """Google Gemini provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ai_settings.google_api_key
        
        if not self.api_key:
            raise ValueError("Google API key is required")
            
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Safety settings - use string-based configuration to avoid import issues
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
    
    def get_provider_name(self) -> AIProvider:
        """Get the provider name."""
        return AIProvider.GOOGLE
    
    def get_supported_models(self) -> List[AIModel]:
        """Get list of supported Gemini models."""
        return [
            AIModel.GEMINI_PRO,
            AIModel.GEMINI_PRO_VISION,
            AIModel.GEMINI_1_5_PRO,
            AIModel.GEMINI_1_5_FLASH,
            AIModel.GEMINI_2_0_FLASH
        ]
    
    async def validate_model(self, model: AIModel) -> bool:
        """Validate if model is supported and accessible."""
        if model not in self.get_supported_models():
            return False
            
        try:
            # Simple validation - check if model is in our supported list
            return model in self.get_supported_models()
        except Exception:
            return False
    
    async def get_model_info(self, model: AIModel) -> Dict[str, Any]:
        """Get information about a specific model."""
        config = get_model_config(model)
        return {
            "model": model.value,
            "provider": self.get_provider_name().value,
            "max_tokens": config.get("max_tokens", 8192),
            "context_length": config.get("context_length", 32768),
            "supports_streaming": config.get("supports_streaming", True),
            "supports_functions": config.get("supports_functions", True),
            "supports_vision": config.get("supports_vision", False),
            "cost_per_1k_tokens": config.get("cost_per_1k_tokens", {})
        }
    
    def _convert_messages(self, messages: List[AIMessage]) -> List[Dict[str, str]]:
        """Convert AIMessage objects to Gemini format."""
        gemini_messages = []
        
        for msg in messages:
            # Gemini uses 'user' and 'model' roles
            if msg.role == MessageRole.USER:
                role = "user"
            elif msg.role == MessageRole.ASSISTANT:
                role = "model"
            elif msg.role == MessageRole.SYSTEM:
                # System messages are handled differently in Gemini
                # We'll prepend them to the first user message
                continue
            else:
                role = "user"  # Default fallback
            
            gemini_messages.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        # Handle system message by prepending to conversation
        system_content = ""
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_content += f"{msg.content}\n\n"
        
        if system_content and gemini_messages:
            # Prepend system content to first user message
            first_user_msg = next((m for m in gemini_messages if m["role"] == "user"), None)
            if first_user_msg:
                first_user_msg["parts"][0]["text"] = system_content + first_user_msg["parts"][0]["text"]
        
        return gemini_messages
    
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate a single response from Gemini."""
        start_time = time.time()
        
        try:
            # Initialize model
            model = genai.GenerativeModel(
                model_name=request.model.value,
                safety_settings=self.safety_settings
            )
            
            # Convert messages
            gemini_messages = self._convert_messages(request.messages)
            
            # Prepare content for generation
            if len(gemini_messages) == 1 and gemini_messages[0]["role"] == "user":
                # Single user message
                content = gemini_messages[0]["parts"][0]["text"]
            else:
                # Multi-turn conversation - use chat
                chat = model.start_chat(history=gemini_messages[:-1])
                content = gemini_messages[-1]["parts"][0]["text"]
                response = chat.send_message(
                    content,
                    generation_config={
                        "temperature": request.temperature or ai_settings.default_temperature,
                        "max_output_tokens": request.max_tokens or ai_settings.default_max_tokens,
                    }
                )
            
            if len(gemini_messages) <= 1:
                # Single turn generation
                response = model.generate_content(
                    content,
                    generation_config={
                        "temperature": request.temperature or ai_settings.default_temperature,
                        "max_output_tokens": request.max_tokens or ai_settings.default_max_tokens,
                    },
                    safety_settings=self.safety_settings
                )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract response content
            response_text = response.text if response.text else ""
            
            # Estimate tokens (Gemini doesn't provide exact counts in all cases)
            estimated_tokens = len(response_text.split()) * 1.3  # Rough estimation
            
            return AIResponse(
                content=response_text,
                model=request.model.value,
                provider=AIProvider.GOOGLE,
                tokens_used=int(estimated_tokens),
                processing_time_ms=processing_time,
                finish_reason="stop",
                function_calls=None,  # TODO: Implement function calling
                metadata={
                    "safety_ratings": [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        }
                        for rating in response.candidates[0].safety_ratings
                    ] if response.candidates else [],
                    "model_used": request.model.value
                }
            )
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def generate_streaming_response(self, request: AIRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming response from Gemini."""
        try:
            # Initialize model
            model = genai.GenerativeModel(
                model_name=request.model.value,
                safety_settings=self.safety_settings
            )
            
            # Convert messages
            gemini_messages = self._convert_messages(request.messages)
            
            # Prepare content for generation
            if len(gemini_messages) == 1 and gemini_messages[0]["role"] == "user":
                # Single user message
                content = gemini_messages[0]["parts"][0]["text"]
                response_stream = model.generate_content(
                    content,
                    generation_config={
                        "temperature": request.temperature or ai_settings.default_temperature,
                        "max_output_tokens": request.max_tokens or ai_settings.default_max_tokens,
                    },
                    safety_settings=self.safety_settings,
                    stream=True
                )
            else:
                # Multi-turn conversation
                chat = model.start_chat(history=gemini_messages[:-1])
                content = gemini_messages[-1]["parts"][0]["text"]
                response_stream = chat.send_message(
                    content,
                    generation_config={
                        "temperature": request.temperature or ai_settings.default_temperature,
                        "max_output_tokens": request.max_tokens or ai_settings.default_max_tokens,
                    },
                    stream=True
                )
            
            full_content = ""
            total_tokens = 0
            
            for chunk in response_stream:
                if chunk.text:
                    delta = chunk.text
                    full_content += delta
                    
                    # Estimate tokens
                    estimated_tokens = len(full_content.split()) * 1.3
                    
                    yield StreamChunk(
                        content=full_content,
                        delta=delta,
                        is_complete=False,
                        tokens_used=0,  # Tokens not available during streaming
                        metadata={
                            "model": request.model.value,
                            "chunk_index": len(full_content)
                        }
                    )
                    
                    # Small delay for better user experience
                    if ai_settings.stream_delay_ms > 0:
                        await asyncio.sleep(ai_settings.stream_delay_ms / 1000.0)
            
            # Final chunk
            final_tokens = int(len(full_content.split()) * 1.3)
            yield StreamChunk(
                content=full_content,
                delta="",
                is_complete=True,
                tokens_used=final_tokens,
                metadata={"finish_reason": "stop"}
            )
            
        except Exception as e:
            # Error chunk
            yield StreamChunk(
                content=f"Error: {str(e)}",
                delta="",
                is_complete=True,
                tokens_used=0,
                metadata={"error": str(e)}
            )