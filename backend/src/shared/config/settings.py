"""
Application Settings and Configuration

Centralized settings management for the application using Pydantic.
Supports environment variables and provides type safety.
"""

from typing import Optional, List
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class ApplicationSettings(BaseSettings):
    """Main application settings"""
    
    # Application Info
    app_name: str = "User Authentication System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str = "postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db"
    database_echo: bool = False
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Auth
    auth_secret_key: str = "CHANGE_ME_IN_PRODUCTION_ENVIRONMENT_USE_STRONG_SECRET_KEY"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 60
    auth_refresh_token_expire_days: int = 7
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@example.com"
    smtp_from_name: str = "User Authentication System"
    smtp_use_tls: bool = True
    
    @property
    def smtp_host(self) -> str:
        """Alias for smtp_server for compatibility"""
        return self.smtp_server
    
    # Security
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    
    # OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_redirect_uri: Optional[str] = None
    password_require_special: bool = True
    
    # Registration
    registration_enabled: bool = True
    registration_require_email_verification: bool = True
    registration_auto_activate: bool = True
    
    # AI Settings
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    replicate_api_key: str = ""
    embedding_model: str = "text-embedding-ada-002"
    llm_model: str = "gpt-3.5-turbo-16k"
    
    # Files and Storage
    upload_dir: str = "./data/uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_file_types: List[str] = ["pdf", "doc", "docx", "txt", "md"]
    
    # Vector DB
    vector_store_type: str = "chroma"
    vector_store_path: str = "./data/chroma_db"
    vector_store_collection: str = "documents"
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    @field_validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        # Basic validation - could be extended with regex
        if not v or not ("://" in v):
            raise ValueError("Invalid database URL format")
        return v


# Global application settings instance
_settings = None


def get_settings() -> ApplicationSettings:
    """Get application settings singleton instance"""
    global _settings
    if _settings is None:
        _settings = ApplicationSettings()
    return _settings


def reload_settings() -> ApplicationSettings:
    """Force reload settings"""
    global _settings
    _settings = ApplicationSettings()
    return _settings


def get_database_url() -> str:
    """Helper to get database URL"""
    return get_settings().database_url


def get_redis_connection_info() -> tuple:
    """Helper to get Redis connection info"""
    settings = get_settings()
    return (settings.redis_host, settings.redis_port, settings.redis_db, settings.redis_password)


def get_redis_url() -> str:
    """Helper to get Redis connection URL"""
    return get_settings().redis_url


def get_jwt_secret() -> str:
    """Helper to get JWT secret key"""
    return get_settings().auth_secret_key
    return get_settings().auth_secret_key