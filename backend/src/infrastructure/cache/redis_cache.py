"""
Redis Cache Configuration

Provides Redis connection and caching infrastructure for the application.
Used for session management, rate limiting, and general caching.
"""

import json
import pickle
from datetime import timedelta, datetime
from typing import Any, Optional, Dict, List
from redis.asyncio import Redis
from redis.exceptions import RedisError

from ...shared.config import get_settings


class RedisConfig:
    """Redis configuration and connection management"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
    
    async def connect(self) -> Redis:
        """Connect to Redis"""
        if self.redis is None:
            self.redis = Redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return self.redis
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None


class CacheService:
    """
    Redis-based caching service for the application.
    
    Provides high-level caching operations with JSON and pickle serialization.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try JSON first, fall back to pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value.encode('latin1'))
                
        except RedisError as e:
            # Log error but don't fail - cache miss is acceptable
            print(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[timedelta] = None
    ) -> bool:
        """Set a value in cache with optional expiration"""
        try:
            # Try JSON first, fall back to pickle
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value).decode('latin1')
            
            if expire:
                await self.redis.setex(key, expire, serialized)
            else:
                await self.redis.set(key, serialized)
            
            return True
            
        except RedisError as e:
            print(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except RedisError as e:
            print(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return await self.redis.exists(key) > 0
        except RedisError as e:
            print(f"Redis exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in cache"""
        try:
            return await self.redis.incrby(key, amount)
        except RedisError as e:
            print(f"Redis increment error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, expire: timedelta) -> bool:
        """Set expiration time for existing key"""
        try:
            return await self.redis.expire(key, expire)
        except RedisError as e:
            print(f"Redis expire error for key {key}: {e}")
            return False


class SessionCache:
    """
    Redis-based session management.
    
    Handles user sessions with automatic expiration and validation.
    """
    
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
    
    async def create_session(
        self, 
        session_id: str, 
        user_id: int,
        session_data: Dict[str, Any],
        expire: timedelta = timedelta(hours=24)
    ) -> bool:
        """Create a new session"""
        session_key = f"{self.session_prefix}{session_id}"
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        
        # Store session data
        session_info = {
            "user_id": user_id,
            "created_at": str(datetime.utcnow()),
            **session_data
        }
        
        await self.cache.set(session_key, session_info, expire)
        
        # Add to user's session list (for multi-session management)
        existing_sessions = await self.cache.get(user_sessions_key) or []
        existing_sessions.append(session_id)
        await self.cache.set(user_sessions_key, existing_sessions, expire)
        
        return True
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self.session_prefix}{session_id}"
        return await self.cache.get(session_key)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"{self.session_prefix}{session_id}"
        
        # Get session to find user_id for cleanup
        session_data = await self.cache.get(session_key)
        if session_data and "user_id" in session_data:
            user_sessions_key = f"{self.user_sessions_prefix}{session_data['user_id']}"
            user_sessions = await self.cache.get(user_sessions_key) or []
            if session_id in user_sessions:
                user_sessions.remove(session_id)
                await self.cache.set(user_sessions_key, user_sessions)
        
        return await self.cache.delete(session_key)
    
    async def delete_all_user_sessions(self, user_id: int) -> bool:
        """Delete all sessions for a user"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        session_ids = await self.cache.get(user_sessions_key) or []
        
        for session_id in session_ids:
            session_key = f"{self.session_prefix}{session_id}"
            await self.cache.delete(session_key)
        
        return await self.cache.delete(user_sessions_key)


class RateLimitCache:
    """
    Redis-based rate limiting.
    
    Implements sliding window rate limiting for API endpoints.
    """
    
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.rate_limit_prefix = "rate_limit:"
    
    async def is_rate_limited(
        self,
        identifier: str,
        max_requests: int,
        window: timedelta
    ) -> tuple[bool, int, int]:
        """
        Check if identifier is rate limited.
        
        Returns:
            (is_limited, current_count, remaining_requests)
        """
        key = f"{self.rate_limit_prefix}{identifier}"
        
        current_count = await self.cache.increment(key)
        if current_count is None:
            return False, 0, max_requests
        
        if current_count == 1:
            # First request in window - set expiration
            await self.cache.expire(key, window)
        
        remaining = max(0, max_requests - current_count)
        is_limited = current_count > max_requests
        
        return is_limited, current_count, remaining


# Global cache instances (configured by dependency injection)
_redis_config: Optional[RedisConfig] = None
_cache_service: Optional[CacheService] = None


async def configure_redis(redis_url: str) -> RedisConfig:
    """Configure Redis connection"""
    global _redis_config, _cache_service
    _redis_config = RedisConfig(redis_url)
    redis_client = await _redis_config.connect()
    _cache_service = CacheService(redis_client)
    return _redis_config


async def get_cache_service() -> CacheService:
    """Get cache service instance"""
    if _cache_service is None:
        raise RuntimeError("Redis not configured. Call configure_redis() first.")
    return _cache_service


async def get_session_cache() -> SessionCache:
    """Get session cache instance"""
    cache = await get_cache_service()
    return SessionCache(cache)


async def get_rate_limit_cache() -> RateLimitCache:
    """Get rate limit cache instance"""
    cache = await get_cache_service()
    return RateLimitCache(cache)