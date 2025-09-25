"""
AI Integration Configuration

This module contains configuration settings for AI providers and models.
"""

from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum
import os

# Explicitly load environment variables
from dotenv import load_dotenv

# Load from the correct backend/.env path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)
print(f"Loading AI config from .env: {env_path}")
print(f"GOOGLE_API_KEY present: {'Yes' if os.environ.get('GOOGLE_API_KEY') else 'No'}")
print(f"ANTHROPIC_API_KEY present: {'Yes' if os.environ.get('ANTHROPIC_API_KEY') else 'No'}")


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    LOCAL = "local"


class AIModel(Enum):
    """Supported AI models."""
    # Google Gemini Models (Primary)
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    
    # Anthropic Models (Fallback)
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_HAIKU = "claude-3-5-haiku-20241022"


class AISettings(BaseSettings):
    """AI integration settings."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    azure_openai_api_key: Optional[str] = Field(default=None, validation_alias="AZURE_OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(default=None, validation_alias="GOOGLE_API_KEY")
    
    # Azure OpenAI specific
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-01"
    
    # Default settings
    default_provider: AIProvider = AIProvider.GOOGLE
    default_model: str = Field(default="gemini-2.0-flash", validation_alias="AI_DEFAULT_MODEL")
    default_max_tokens: int = Field(default=4000, validation_alias="AI_MAX_TOKENS")
    default_temperature: float = Field(default=0.7, validation_alias="AI_DEFAULT_TEMPERATURE")
    
    # Streaming settings
    enable_streaming: bool = Field(default=True, validation_alias="AI_ENABLE_STREAMING")
    stream_chunk_size: int = 1
    stream_delay_ms: int = 50
    
    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 150000
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Content filtering
    enable_content_filtering: bool = True
    content_filter_threshold: float = 0.8
    
    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields from .env
    }


# Model configurations
MODEL_CONFIGS: Dict[AIModel, Dict[str, Any]] = {
    # Google Gemini Models (Primary)
    AIModel.GEMINI_PRO: {
        "provider": AIProvider.GOOGLE,
        "max_tokens": 8192,
        "context_length": 32768,
        "supports_streaming": True,
        "supports_functions": True,
        "cost_per_1k_tokens": {"input": 0.00025, "output": 0.0005}
    },
    AIModel.GEMINI_PRO_VISION: {
        "provider": AIProvider.GOOGLE,
        "max_tokens": 8192,
        "context_length": 32768,
        "supports_streaming": True,
        "supports_functions": True,
        "supports_vision": True,
        "cost_per_1k_tokens": {"input": 0.00025, "output": 0.0005}
    },
    AIModel.GEMINI_1_5_PRO: {
        "provider": AIProvider.GOOGLE,
        "max_tokens": 8192,
        "context_length": 1000000,  # 1M context
        "supports_streaming": True,
        "supports_functions": True,
        "cost_per_1k_tokens": {"input": 0.00125, "output": 0.00375}
    },
    AIModel.GEMINI_1_5_FLASH: {
        "provider": AIProvider.GOOGLE,
        "max_tokens": 8192,
        "context_length": 1000000,  # 1M context
        "supports_streaming": True,
        "supports_functions": True,
        "cost_per_1k_tokens": {"input": 0.000075, "output": 0.0003}
    },
    AIModel.GEMINI_2_0_FLASH: {
        "provider": AIProvider.GOOGLE,
        "max_tokens": 8192,
        "context_length": 1000000,  # 1M context
        "supports_streaming": True,
        "supports_functions": True,
        "cost_per_1k_tokens": {"input": 0.000075, "output": 0.0003}  # Estimated pricing
    },
    
    # Anthropic Models (Fallback)
    AIModel.CLAUDE_3_5_SONNET: {
        "provider": AIProvider.ANTHROPIC,
        "max_tokens": 4096,
        "context_length": 200000,
        "supports_streaming": True,
        "supports_functions": False,
        "cost_per_1k_tokens": {"input": 0.003, "output": 0.015}
    },
    AIModel.CLAUDE_3_OPUS: {
        "provider": AIProvider.ANTHROPIC,
        "max_tokens": 4096,
        "context_length": 200000,
        "supports_streaming": True,
        "supports_functions": False,
        "cost_per_1k_tokens": {"input": 0.015, "output": 0.075}
    },
    AIModel.CLAUDE_3_HAIKU: {
        "provider": AIProvider.ANTHROPIC,
        "max_tokens": 4096,
        "context_length": 200000,
        "supports_streaming": True,
        "supports_functions": False,
        "cost_per_1k_tokens": {"input": 0.00025, "output": 0.00125}
    },
}


def get_model_config(model: AIModel) -> Dict[str, Any]:
    """Get configuration for a specific AI model."""
    return MODEL_CONFIGS.get(model, MODEL_CONFIGS[AIModel.GEMINI_PRO])


def get_provider_for_model(model: AIModel) -> AIProvider:
    """Get the provider for a specific model."""
    config = get_model_config(model)
    return config["provider"]


def is_streaming_supported(model: AIModel) -> bool:
    """Check if streaming is supported for a model."""
    config = get_model_config(model)
    return config.get("supports_streaming", False)


# Global settings instance
ai_settings = AISettings()