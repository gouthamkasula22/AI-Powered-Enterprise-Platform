"""
Anthropic Claude Provider Implementation

This module provides the Anthropic Claude integration for AI services.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncIterator, AsyncGenerator
import json
import httpx
from datetime import datetime

from ....domain.ai.interfaces import (
    AIProviderInterface, AIRequest, AIResponse, StreamChunk, 
    AIMessage, MessageRole
)
from ..config import AIProvider, AIModel, ai_settings, get_model_config


class AnthropicProvider(AIProviderInterface):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ai_settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com"
        self.api_version = "2023-06-01"
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
    
    def get_provider_name(self) -> AIProvider:
        """Get the provider name."""
        return AIProvider.ANTHROPIC
    
    def get_supported_models(self) -> List[AIModel]:
        """Get list of supported Claude models."""
        return [
            AIModel.CLAUDE_3_5_SONNET,
            AIModel.CLAUDE_3_OPUS,
            AIModel.CLAUDE_3_HAIKU
        ]
    
    async def validate_model(self, model: AIModel) -> bool:
        """Validate if model is supported and accessible."""
        if model not in self.get_supported_models():
            return False
            
        try:
            # Simple validation request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "x-api-key": self.api_key or "",
                        "anthropic-version": self.api_version,
                        "content-type": "application/json"
                    },
                    json={
                        "model": model.value,
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "test"}]
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_model_info(self, model: AIModel) -> Dict[str, Any]:
        """Get information about a specific model."""
        config = get_model_config(model)
        return {
            "model": model.value,
            "provider": self.get_provider_name().value,
            "max_tokens": config.get("max_tokens", 4096),
            "context_length": config.get("context_length", 200000),
            "supports_streaming": config.get("supports_streaming", True),
            "supports_functions": config.get("supports_functions", False),
            "cost_per_1k_tokens": config.get("cost_per_1k_tokens", {})
        }
    
    def _convert_messages(self, messages: List[AIMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert AIMessage objects to Anthropic format."""
        system_message = None
        claude_messages = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Claude handles system messages separately
                system_message = msg.content
            elif msg.role == MessageRole.USER:
                claude_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == MessageRole.ASSISTANT:
                claude_messages.append({
                    "role": "assistant", 
                    "content": msg.content
                })
        
        return system_message, claude_messages
    
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate a single response from Claude."""
        start_time = time.time()
        
        system_message, claude_messages = self._convert_messages(request.messages)
        
        payload = {
            "model": request.model.value,
            "max_tokens": request.max_tokens or ai_settings.default_max_tokens,
            "messages": claude_messages,
            "temperature": request.temperature or ai_settings.default_temperature
        }
        
        if system_message:
            payload["system"] = system_message
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key or "",
                    "anthropic-version": self.api_version,
                    "content-type": "application/json"
                },
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Anthropic API error {response.status_code}: {error_detail}")
            
            data = response.json()
            usage = data.get("usage", {})
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract content from response
            content = ""
            if data.get("content"):
                for content_block in data["content"]:
                    if content_block.get("type") == "text":
                        content += content_block.get("text", "")
            
            return AIResponse(
                content=content,
                model=request.model.value,
                provider=AIProvider.ANTHROPIC,
                tokens_used=usage.get("output_tokens", 0) + usage.get("input_tokens", 0),
                processing_time_ms=processing_time,
                finish_reason=data.get("stop_reason", "stop"),
                function_calls=None,  # Claude doesn't support function calls in the same way
                metadata={
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "stop_reason": data.get("stop_reason"),
                    "stop_sequence": data.get("stop_sequence"),
                    "model_used": data.get("model", request.model.value)
                }
            )
    
    async def generate_streaming_response(self, request: AIRequest) -> AsyncGenerator[StreamChunk, None]:  # type: ignore
        """Generate a streaming response from Claude."""
        system_message, claude_messages = self._convert_messages(request.messages)
        
        payload = {
            "model": request.model.value,
            "max_tokens": request.max_tokens or ai_settings.default_max_tokens,
            "messages": claude_messages,
            "temperature": request.temperature or ai_settings.default_temperature,
            "stream": True
        }
        
        if system_message:
            payload["system"] = system_message
        
        full_content = ""
        total_tokens = 0
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key or "",
                    "anthropic-version": self.api_version,
                    "content-type": "application/json"
                },
                json=payload
            ) as response:
                
                if response.status_code != 200:
                    error_detail = await response.aread()
                    raise Exception(f"Anthropic API error {response.status_code}: {error_detail}")
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str.strip() == "[DONE]":
                            # Final chunk
                            yield StreamChunk(
                                content=full_content,
                                delta="",
                                is_complete=True,
                                tokens_used=total_tokens,
                                metadata={"finish_reason": "stop"}
                            )
                            return
                        
                        try:
                            event_data = json.loads(data_str)
                            
                            # Handle different event types
                            if event_data.get("type") == "content_block_delta":
                                delta_data = event_data.get("delta", {})
                                if delta_data.get("type") == "text_delta":
                                    delta = delta_data.get("text", "")
                                    full_content += delta
                                    
                                    yield StreamChunk(
                                        content=full_content,
                                        delta=delta,
                                        is_complete=False,
                                        tokens_used=0,  # Tokens not available during streaming
                                        metadata={
                                            "model": request.model.value,
                                            "event_type": event_data.get("type")
                                        }
                                    )
                                    
                                    # Small delay for better user experience
                                    if ai_settings.stream_delay_ms > 0:
                                        await asyncio.sleep(ai_settings.stream_delay_ms / 1000.0)
                            
                            elif event_data.get("type") == "message_delta":
                                # Handle usage information
                                usage = event_data.get("usage", {})
                                total_tokens = usage.get("output_tokens", 0)
                                
                        except json.JSONDecodeError:
                            # Skip malformed JSON
                            continue