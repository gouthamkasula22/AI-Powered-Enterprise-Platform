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
    
    # JWT Security
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Email SMTP
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@example.com"
    smtp_from_name: str = "Authentication System"
    
    # Password Security
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    account_lockout_minutes: int = 15
    
    # OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_redirect_uri: Optional[str] = None
    
    # API Settings
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    frontend_url: str = "http://localhost:3000"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # Handle both comma-separated and JSON array format
            if v.startswith('[') and v.endswith(']'):
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
_settings: Optional[ApplicationSettings] = None


def get_settings() -> ApplicationSettings:
    """
    Get application settings singleton
    
    Returns:
        ApplicationSettings instance
    """
    global _settings
    if _settings is None:
        _settings = ApplicationSettings()
    return _settings


def reload_settings() -> ApplicationSettings:
    """
    Reload settings from environment
    
    Returns:
        Fresh ApplicationSettings instance
    """
    global _settings
    _settings = ApplicationSettings()
    return _settings


# Convenience functions for common settings
def get_database_url() -> str:
    """Get database connection URL"""
    return get_settings().database_url


def get_redis_url() -> str:
    """Get Redis connection URL"""
    return get_settings().redis_url


def get_jwt_secret() -> str:
    """Get JWT secret key"""
    return get_settings().jwt_secret_key


def is_development() -> bool:
    """Check if running in development mode"""
    return get_settings().environment.lower() == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return get_settings().environment.lower() == "production"