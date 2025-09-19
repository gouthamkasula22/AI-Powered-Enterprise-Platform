"""
Cache Manager

Centralized cache management for the application.
Provides unified access to all caching services and handles initialization.
"""

import logging
from typing import Optional
from redis.asyncio import Redis

from .redis_cache import (
    RedisConfig, CacheService, SessionCache, RateLimitCache,
    configure_redis, get_cache_service
)
from .token_blacklist import TokenBlacklistService, UserCacheService
from ...shared.config import get_settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache manager for all caching services.
    
    Manages Redis connection and provides access to specialized cache services.
    """
    
    def __init__(self):
        self._redis_config: Optional[RedisConfig] = None
        self._cache_service: Optional[CacheService] = None
        self._session_cache: Optional[SessionCache] = None
        self._rate_limit_cache: Optional[RateLimitCache] = None
        self._token_blacklist: Optional[TokenBlacklistService] = None
        self._user_cache: Optional[UserCacheService] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all cache services"""
        if self._initialized:
            return
        
        try:
            settings = get_settings()
            
            # Configure Redis connection
            self._redis_config = await configure_redis(settings.redis_url)
            self._cache_service = await get_cache_service()
            
            # Initialize specialized cache services
            self._session_cache = SessionCache(self._cache_service)
            self._rate_limit_cache = RateLimitCache(self._cache_service)
            self._token_blacklist = TokenBlacklistService(self._cache_service)
            self._user_cache = UserCacheService(self._cache_service)
            
            self._initialized = True
            logger.info("Cache manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    async def close(self) -> None:
        """Close cache connections"""
        try:
            if self._redis_config:
                await self._redis_config.disconnect()
            self._initialized = False
            logger.info("Cache manager closed")
        except Exception as e:
            logger.error(f"Error closing cache manager: {e}")
    
    @property
    def cache_service(self) -> CacheService:
        """Get general cache service"""
        if not self._initialized or not self._cache_service:
            raise RuntimeError("Cache manager not initialized")
        return self._cache_service
    
    @property
    def session_cache(self) -> SessionCache:
        """Get session cache service"""
        if not self._initialized or not self._session_cache:
            raise RuntimeError("Cache manager not initialized")
        return self._session_cache
    
    @property
    def rate_limit_cache(self) -> RateLimitCache:
        """Get rate limit cache service"""
        if not self._initialized or not self._rate_limit_cache:
            raise RuntimeError("Cache manager not initialized")
        return self._rate_limit_cache
    
    @property
    def token_blacklist(self) -> TokenBlacklistService:
        """Get token blacklist service"""
        if not self._initialized or not self._token_blacklist:
            raise RuntimeError("Cache manager not initialized")
        return self._token_blacklist
    
    @property
    def user_cache(self) -> UserCacheService:
        """Get user cache service"""
        if not self._initialized or not self._user_cache:
            raise RuntimeError("Cache manager not initialized")
        return self._user_cache
    
    @property
    def is_initialized(self) -> bool:
        """Check if cache manager is initialized"""
        return self._initialized
    
    async def health_check(self) -> dict:
        """
        Check cache health and connectivity
        
        Returns:
            Dict with health information
        """
        try:
            if not self._initialized or self._cache_service is None:
                return {
                    "status": "unhealthy",
                    "redis": "not_initialized",
                    "message": "Cache manager not initialized"
                }
            
            # Test Redis connectivity with a simple operation
            test_key = "health_check"
            await self._cache_service.set(test_key, "test", None)
            result = await self._cache_service.get(test_key)
            await self._cache_service.delete(test_key)
            
            if result == "test":
                return {
                    "status": "healthy",
                    "redis": "connected",
                    "services": {
                        "cache": "available",
                        "sessions": "available",
                        "rate_limiting": "available",
                        "token_blacklist": "available",
                        "user_cache": "available"
                    },
                    "message": "All cache services operational"
                }
            else:
                return {
                    "status": "degraded",
                    "redis": "connected",
                    "message": "Cache operations not working correctly"
                }
                
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "redis": "disconnected",
                "message": f"Cache error: {str(e)}"
            }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


async def initialize_cache() -> None:
    """Initialize the cache manager (call during app startup)"""
    cache_manager = get_cache_manager()
    await cache_manager.initialize()


async def close_cache() -> None:
    """Close cache connections (call during app shutdown)"""
    cache_manager = get_cache_manager()
    await cache_manager.close()


# FastAPI dependencies
async def get_cache_service_dep() -> CacheService:
    """FastAPI dependency for cache service"""
    cache_manager = get_cache_manager()
    return cache_manager.cache_service


async def get_session_cache_dep() -> SessionCache:
    """FastAPI dependency for session cache"""
    cache_manager = get_cache_manager()
    return cache_manager.session_cache


async def get_rate_limit_cache_dep() -> RateLimitCache:
    """FastAPI dependency for rate limit cache"""
    cache_manager = get_cache_manager()
    return cache_manager.rate_limit_cache


async def get_token_blacklist_dep() -> TokenBlacklistService:
    """FastAPI dependency for token blacklist service"""
    cache_manager = get_cache_manager()
    return cache_manager.token_blacklist


async def get_user_cache_dep() -> UserCacheService:
    """FastAPI dependency for user cache service"""
    cache_manager = get_cache_manager()
    return cache_manager.user_cache