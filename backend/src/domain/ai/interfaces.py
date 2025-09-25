"""
AI Service Interfaces

This module defines the interfaces for AI services and providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, AsyncGenerator, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ...infrastructure.ai.config import AIProvider, AIModel


class MessageRole(Enum):
    """Message roles in AI conversation."""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class AIMessage:
    """Represents a message in AI conversation."""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    function_call: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


@dataclass
class AIResponse:
    """Represents an AI response."""
    content: str
    model: str
    provider: AIProvider
    tokens_used: int
    processing_time_ms: int
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None
    function_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class StreamChunk:
    """Represents a streaming chunk from AI."""
    content: str
    delta: str
    is_complete: bool
    tokens_used: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIRequest:
    """Represents a request to AI provider."""
    messages: List[AIMessage]
    model: AIModel
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class AIProviderInterface(ABC):
    """Abstract interface for AI providers."""
    
    @abstractmethod
    def get_provider_name(self) -> AIProvider:
        """Get the provider name."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[AIModel]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    async def generate_response(self, request: AIRequest) -> AIResponse:
        """Generate a single response."""
        pass
    
    @abstractmethod
    async def generate_streaming_response(self, request: AIRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming response."""
        pass
    
    @abstractmethod
    async def validate_model(self, model: AIModel) -> bool:
        """Validate if model is supported and accessible."""
        pass
    
    @abstractmethod
    async def get_model_info(self, model: AIModel) -> Dict[str, Any]:
        """Get information about a specific model."""
        pass


class AIServiceInterface(ABC):
    """Abstract interface for AI service."""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[AIMessage],
        model: Optional[AIModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Generate a single AI response."""
        pass
    
    @abstractmethod
    async def generate_streaming_response(
        self,
        messages: List[AIMessage], 
        model: Optional[AIModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming AI response."""
        pass
    
    @abstractmethod
    async def get_conversation_summary(
        self,
        messages: List[AIMessage],
        max_length: int = 200
    ) -> str:
        """Generate a summary of the conversation."""
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[AIModel]:
        """Get list of available models."""
        pass
    
    @abstractmethod
    def get_provider_for_model(self, model: AIModel) -> AIProvider:
        """Get the provider for a specific model."""
        pass


class ContentModerationInterface(ABC):
    """Interface for content moderation."""
    
    @abstractmethod
    async def moderate_content(self, content: str) -> Dict[str, Any]:
        """Moderate content and return safety analysis."""
        pass
    
    @abstractmethod
    async def is_content_safe(self, content: str, threshold: float = 0.8) -> bool:
        """Check if content is safe based on threshold."""
        pass


class FunctionCallingInterface(ABC):
    """Interface for AI function calling capabilities."""
    
    @abstractmethod
    async def execute_function_call(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a function call from AI."""
        pass
    
    @abstractmethod
    def get_available_functions(self) -> List[Dict[str, Any]]:
        """Get list of available functions for AI."""
        pass
    
    @abstractmethod
    def register_function(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any]
    ) -> None:
        """Register a new function for AI to call."""
        pass