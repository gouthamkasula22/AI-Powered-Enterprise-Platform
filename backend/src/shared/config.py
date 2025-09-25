"""
Application Settings and Configuration

This is a forwarding module to avoid breaking existing imports.
The actual settings implementation has been moved to the config package.
"""

# Forward the imports from the config package
from .config.settings import (
    ApplicationSettings,
    get_settings,
    reload_settings,
    get_database_url,
    get_redis_connection_info,
    get_redis_url,
    get_jwt_secret
)

# For backward compatibility
__all__ = [
    "ApplicationSettings",
    "get_settings",
    "reload_settings",
    "get_database_url",
    "get_redis_connection_info",
    "get_redis_url",
    "get_jwt_secret"
]

# Create a settings instance for easy access
settings = get_settings()


def is_development() -> bool:
    """Check if running in development mode"""
    return get_settings().environment.lower() == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return get_settings().environment.lower() == "production"