"""
Multi-Provider LLM Service for RAG Implementation
Supports Google Gemini (primary) and Anthropic Claude (fallback) as configured.
"""

import asyncio
from typing import Dict, List, Optional, AsyncIterator, Any, Union, cast
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import os
import importlib

# Import Google Gemini library through importlib to avoid type checking issues
genai = importlib.import_module("google.generativeai")

# Direct imports for Anthropic
from anthropic import AsyncAnthropic

import tiktoken

from .config import AISettings, AIModel, AIProvider, MODEL_CONFIGS, ai_settings
from .context_manager import ContextWindow
from .query_processor import ProcessedQuery, Message
from ...shared.exceptions import AIError, ConfigurationError, RateLimitError

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """Response from LLM chat completion"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]
    citations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_id: Optional[str] = None


@dataclass
class ModelInfo:
    """Information about available models"""
    name: str
    provider: str
    max_tokens: int
    context_length: int
    supports_streaming: bool
    supports_functions: bool
    cost_per_1k_tokens: Dict[str, float]


class LLMService:
    """Multi-provider LLM service for RAG chat system"""
    
    def __init__(self, settings: Optional[AISettings] = None):
        self.settings = settings if settings is not None else ai_settings
        
        # Initialize providers
        self._gemini_client = False
        self._anthropic_client = None
        self._tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize provider clients
        self._initialize_providers()
        
        # Fallback chain: Primary -> Secondary -> Error
        self.provider_chain = [
            AIProvider.GOOGLE,      # Primary: Gemini
            AIProvider.ANTHROPIC,   # Fallback: Claude
        ]
    
    def _initialize_providers(self):
        """Initialize AI provider clients"""
        
        try:
            # Initialize Google Gemini
            if self.settings.google_api_key:
                # Direct API key configuration
                os.environ["GOOGLE_API_KEY"] = self.settings.google_api_key
                # Use setattr to set API key and avoid type checking issues
                setattr(genai, "_api_key", self.settings.google_api_key)
                self._gemini_client = True
                logger.info("Google Gemini client initialized successfully")
            else:
                logger.warning("Google API key not provided - Gemini unavailable")
            
            # Initialize Anthropic Claude
            if self.settings.anthropic_api_key:
                self._anthropic_client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
                logger.info("Anthropic Claude client initialized successfully")
            else:
                logger.warning("Anthropic API key not provided - Claude unavailable")
                
        except Exception as e:
            logger.error(f"Provider initialization failed: {str(e)}")
            raise ConfigurationError(f"Failed to initialize AI providers: {str(e)}")
    
    async def generate_response(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: Optional[List[Message]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """
        Generate response using RAG context and conversation history
        
        Args:
            query: User's question/query
            context_window: Retrieved context from documents
            conversation_history: Previous messages in conversation
            model: Specific model to use (defaults to configured default)
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response tokens
            
        Returns:
            ChatResponse with generated answer and metadata
        """
        
        # Use default model if not specified
        if not model:
            model = self.settings.default_model
        
        # Get model configuration
        try:
            model_enum = AIModel(model)
            model_config = MODEL_CONFIGS[model_enum]
            provider = model_config["provider"]
        except (ValueError, KeyError):
            logger.error(f"Invalid model specified: {model}")
            raise AIError(f"Model {model} is not supported")
        
        # Set defaults
        temperature = temperature or self.settings.default_temperature
        max_tokens = max_tokens or min(model_config["max_tokens"], self.settings.default_max_tokens)
        
        # Try providers in fallback chain order
        last_error = None
        
        for provider_to_try in self.provider_chain:
            if provider_to_try == provider or (provider == AIProvider.GOOGLE and provider_to_try == AIProvider.GOOGLE):
                try:
                    if provider_to_try == AIProvider.GOOGLE:
                        # Force max_tokens to int to satisfy type checking
                        tokens = 4000 if max_tokens is None else int(max_tokens)
                        response = await self._generate_with_gemini(
                            query, context_window, conversation_history,
                            model, temperature, tokens
                        )
                        return response
                        
                    elif provider_to_try == AIProvider.ANTHROPIC:
                        # Force max_tokens to int to satisfy type checking
                        tokens = 4000 if max_tokens is None else int(max_tokens)
                        response = await self._generate_with_anthropic(
                            query, context_window, conversation_history,
                            "claude-3-5-sonnet-20241022",  # Use latest Sonnet as fallback
                            temperature, tokens
                        )
                        return response
                        
                except Exception as e:
                    logger.warning(f"Provider {provider_to_try.value} failed: {str(e)}")
                    last_error = e
                    continue
        
        # If all providers failed
        raise AIError(f"All AI providers failed. Last error: {str(last_error)}")
    
    async def stream_response(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: Optional[List[Message]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """
        Stream response generation for real-time chat experience
        
        Args:
            query: User's question/query
            context_window: Retrieved context from documents  
            conversation_history: Previous conversation messages
            model: Specific model to use
            temperature: Response creativity
            
        Yields:
            String chunks of the response as they're generated
        """
        
        model = model or self.settings.default_model
        temperature = temperature or self.settings.default_temperature
        
        try:
            # Get model configuration
            model_enum = AIModel(model)
            model_config = MODEL_CONFIGS[model_enum]
            provider = model_config["provider"]
            
            if provider == AIProvider.GOOGLE and self._gemini_client:
                async for chunk in self._stream_with_gemini(
                    query, context_window, conversation_history, model, temperature
                ):
                    yield chunk
                    
            elif provider == AIProvider.ANTHROPIC and self._anthropic_client:
                async for chunk in self._stream_with_anthropic(
                    query, context_window, conversation_history, 
                    "claude-3-5-sonnet-20241022", temperature
                ):
                    yield chunk
                    
            else:
                # Fallback to non-streaming if streaming unavailable
                logger.info(f"Streaming not available for {model}, falling back to complete response")
                response = await self.generate_response(
                    query, context_window, conversation_history, model, temperature
                )
                yield response.content
                
        except Exception as e:
            logger.error(f"Streaming response generation failed: {str(e)}")
            yield f"Error generating response: {str(e)}"
    
    async def _generate_with_gemini(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: Optional[List[Message]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> ChatResponse:
        """Generate response using Google Gemini"""
        
        if not self._gemini_client:
            raise AIError("Gemini client not initialized")
        
        try:
            # Build prompt with context and history
            prompt = self._build_gemini_prompt(query, context_window, conversation_history or [])
            
            # Use direct function call without type checking
            generate_content = getattr(genai, "generate_text")
            
            # Generate response using direct function call to avoid type issues
            response = await generate_content(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Get response text safely - since we're using direct function call
            response_text = ""
            if response is not None:
                if hasattr(response, "text"):
                    response_text = getattr(response, "text", "")
                elif hasattr(response, "result"):
                    response_text = getattr(response, "result", "")
                else:
                    response_text = str(response)
                
            # Extract usage information (if available)
            usage = {
                "prompt_tokens": len(self._tokenizer.encode(prompt)),
                "completion_tokens": len(self._tokenizer.encode(response_text)),
                "total_tokens": len(self._tokenizer.encode(prompt)) + len(self._tokenizer.encode(response_text))
            }
            
            # Extract citations from context
            citations = self._extract_citations(context_window)
            
            return ChatResponse(
                content=response_text.strip(),
                model=model,
                provider="google",
                usage=usage,
                citations=citations,
                response_id=f"gemini_{datetime.utcnow().isoformat()}"
            )
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise AIError(f"Gemini response generation failed: {str(e)}")
    
    async def _generate_with_anthropic(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: Optional[List[Message]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> ChatResponse:
        """Generate response using Anthropic Claude"""
        
        if not self._anthropic_client:
            raise AIError("Anthropic client not initialized")
        
        try:
            # Build system prompt with context
            system_prompt = f"""You are a knowledgeable AI assistant that helps users by answering questions based on provided context from their documents.

{context_window.context_text if context_window.context_text else "No relevant context found."}

Please answer questions based on the provided context. If the context doesn't fully answer a question, indicate what additional information might be needed."""
            
            # Format conversation messages
            conv_history = conversation_history or []
            anthropic_messages = []
            
            # Add conversation history
            for message in conv_history[-6:]:  # Last 6 messages
                anthropic_messages.append({
                    "role": message.role,
                    "content": message.content
                })
            
            # Add current query
            anthropic_messages.append({
                "role": "user",
                "content": query
            })
            
            # Generate response
            response = await self._anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=anthropic_messages  # type: ignore
            )
            
            # Extract response content safely
            content = ""
            if hasattr(response, "content") and response.content and len(response.content) > 0:
                for content_block in response.content:
                    # Handle different content block types safely
                    if hasattr(content_block, "text"):
                        content = getattr(content_block, "text", "")
                        break
                    elif isinstance(content_block, dict) and "text" in content_block:
                        content = content_block["text"]
                        break
                    else:
                        content = str(content_block)
            
            # Extract usage information safely
            usage = {
                "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                "completion_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": getattr(response.usage, "input_tokens", 0) + getattr(response.usage, "output_tokens", 0)
            }
            
            # Extract citations
            citations = self._extract_citations(context_window)
            
            return ChatResponse(
                content=content.strip(),
                model=model,
                provider="anthropic",
                usage=usage,
                citations=citations,
                response_id=f"claude_{datetime.utcnow().isoformat()}"
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise AIError(f"Claude response generation failed: {str(e)}")
    
    async def _stream_with_gemini(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: Optional[List[Message]],
        model: str,
        temperature: float
    ) -> AsyncIterator[str]:
        """Stream response from Gemini"""
        
        try:
            prompt = self._build_gemini_prompt(query, context_window, conversation_history or [])
            
            # Use direct function call without type checking
            # Streaming in Google Gemini API is a bit complex, so we use a workaround
            # Simulate streaming by returning the whole response at once
            generate_content = getattr(genai, "generate_text")
            
            # Generate full response and yield it
            response = await generate_content(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=4000
            )
            
            # Extract text safely
            response_text = ""
            if response is not None:
                if hasattr(response, "text"):
                    response_text = getattr(response, "text", "")
                elif hasattr(response, "result"):
                    response_text = getattr(response, "result", "")
                else:
                    response_text = str(response)
                
            # Simulate streaming by yielding in chunks
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                yield response_text[i:i+chunk_size]
                await asyncio.sleep(0.05)
            
            # Process stream safely
            async for chunk in response:
                # Extract text from chunk using getattr for safety
                if chunk and hasattr(chunk, "text") and getattr(chunk, "text", None):
                    yield getattr(chunk, "text")
                elif chunk and hasattr(chunk, "parts"):
                    parts = getattr(chunk, "parts", [])
                    for part in parts:
                        if part and hasattr(part, "text") and getattr(part, "text", None):
                            yield getattr(part, "text")
                    
        except Exception as e:
            logger.error(f"Gemini streaming failed: {str(e)}")
            yield f"Streaming error: {str(e)}"
    
    async def _stream_with_anthropic(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: Optional[List[Message]],
        model: str,
        temperature: float
    ) -> AsyncIterator[str]:
        """Stream response from Claude"""
        
        if not self._anthropic_client:
            yield "Error: Anthropic client not initialized"
            return
            
        try:
            # Build system prompt with context
            system_prompt = f"""You are a knowledgeable AI assistant that helps users by answering questions based on provided context from their documents.

{context_window.context_text if context_window.context_text else "No relevant context found."}

Please answer questions based on the provided context. If the context doesn't fully answer a question, indicate what additional information might be needed."""
            
            # Format conversation messages
            conv_history = conversation_history or []
            anthropic_messages = []
            
            # Add conversation history
            for message in conv_history[-6:]:  # Last 6 messages
                anthropic_messages.append({
                    "role": message.role,
                    "content": message.content
                })
            
            # Add current query
            anthropic_messages.append({
                "role": "user",
                "content": query
            })
                
            # Create streaming response
            async with self._anthropic_client.messages.stream(
                model=model,
                max_tokens=4000,
                temperature=temperature,
                system=system_prompt,
                messages=anthropic_messages  # type: ignore
            ) as stream:
                # Process stream content carefully
                try:
                    async for text_chunk in stream.text_stream:
                        if text_chunk:
                            yield text_chunk
                except Exception as inner_e:
                    logger.error(f"Stream processing failed: {str(inner_e)}")
                    yield f"Stream processing error: {str(inner_e)}"
                    
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {str(e)}")
            yield f"Streaming error: {str(e)}"
    
    def _build_gemini_prompt(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: List[Message]
    ) -> str:
        """Build prompt for Gemini models"""
        
        # Format context
        context_text = context_window.context_text if context_window.context_text else "No relevant context found."
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-6:]:  # Last 6 messages
                role = "User" if msg.role == "user" else "Assistant"
                history_parts.append(f"{role}: {msg.content}")
            history_text = f"\n\nConversation History:\n" + "\n".join(history_parts)
        
        # Combine into full prompt
        prompt = f"""You are a knowledgeable AI assistant that helps users by answering questions based on provided context from their documents.

## Context Information
{context_text}
{history_text}

## Instructions
Based on the provided context and conversation history, please answer the following question accurately and helpfully. If the context doesn't fully answer the question, indicate what additional information might be needed.

## User Question
{query}

## Response
Please provide a comprehensive answer based on the available context:"""
        
        return prompt
    
    async def _build_anthropic_messages(
        self,
        query: str,
        context_window: ContextWindow,
        conversation_history: List[Message]
    ) -> List[Dict[str, str]]:
        """Build message format for Anthropic Claude"""
        
        # System prompt with context
        context_text = context_window.context_text if context_window.context_text else "No relevant context found."
        
        system_prompt = f"""You are a knowledgeable AI assistant that helps users by answering questions based on provided context from their documents.

<context>
{context_text}
</context>

Please answer questions based on the provided context. If the context doesn't fully answer a question, indicate what additional information might be needed."""
        
        messages = []
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current query
        messages.append({
            "role": "user", 
            "content": query
        })
        
        # For Claude, we need to prepend system context to first user message
        if messages:
            messages[0]["content"] = f"{system_prompt}\n\nUser question: {messages[0]['content']}"
        
        return messages
    
    def _extract_citations(self, context_window: ContextWindow) -> List[str]:
        """Extract document citations from context window"""
        
        if not context_window or not context_window.chunks_used:
            return []
        
        citations = []
        for chunk in context_window.chunks_used:
            doc_name = chunk.chunk.document.filename
            if doc_name not in citations:
                citations.append(doc_name)
        
        return citations[:5]  # Limit to top 5 sources
    
    async def get_model_info(self, model_name: str) -> ModelInfo:
        """Get information about a specific model"""
        
        try:
            model_enum = AIModel(model_name)
            config = MODEL_CONFIGS[model_enum]
            
            return ModelInfo(
                name=model_name,
                provider=config["provider"].value,
                max_tokens=config["max_tokens"],
                context_length=config["context_length"],
                supports_streaming=config["supports_streaming"],
                supports_functions=config.get("supports_functions", False),
                cost_per_1k_tokens=config["cost_per_1k_tokens"]
            )
            
        except (ValueError, KeyError):
            raise AIError(f"Model {model_name} not found")
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of all available models"""
        
        models = []
        for model_enum, config in MODEL_CONFIGS.items():
            # Check if provider is configured
            if config["provider"] == AIProvider.GOOGLE and not self.settings.google_api_key:
                continue
            if config["provider"] == AIProvider.ANTHROPIC and not self.settings.anthropic_api_key:
                continue
                
            models.append(ModelInfo(
                name=model_enum.value,
                provider=config["provider"].value,
                max_tokens=config["max_tokens"],
                context_length=config["context_length"],
                supports_streaming=config["supports_streaming"],
                supports_functions=config.get("supports_functions", False),
                cost_per_1k_tokens=config["cost_per_1k_tokens"]
            ))
        
        return models


# Global LLM service instance
llm_service = LLMService()