"""
Application Configuration
Environment variables and settings management
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "User Authentication System"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, production, test
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db"
    DATABASE_ECHO: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@localhost"
    
    # OAuth Providers
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    
    # Redis (for caching and rate limiting)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Database Configuration
    @property
    def DB_POOL_SIZE(self) -> int:
        return 20 if self.ENVIRONMENT == "production" else 5
    
    @property
    def DB_MAX_OVERFLOW(self) -> int:
        return 30 if self.ENVIRONMENT == "production" else 10
    
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # 1 hour
    DB_POOL_PRE_PING: bool = True
    
    @property
    def DB_ECHO(self) -> bool:
        return self.DEBUG and self.ENVIRONMENT != "production"
    
    DB_ECHO_POOL: bool = False
    DB_STATEMENT_TIMEOUT: int = 30000  # 30 seconds in milliseconds
    DB_QUERY_CACHE_SIZE: int = 1000
    DB_COMPILED_CACHE_SIZE: int = 1000
    
    # Database Connection Options
    DB_CONNECT_TIMEOUT: int = 10
    DB_COMMAND_TIMEOUT: int = 60
    DB_SERVER_SIDE_CURSORS: bool = True
    
    model_config = {"env_file": ".env", "case_sensitive": True}

# Global settings instance
settings = Settings()
