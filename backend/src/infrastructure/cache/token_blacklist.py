"""
JWT Token Blacklist Service

Manages blacklisted JWT tokens for secure logout and token invalidation.
Uses Redis for fast lookups and automatic expiration.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Set, List
from redis.asyncio import Redis

from ..cache.redis_cache import CacheService
from ...shared.config import get_settings


class TokenBlacklistService:
    """
    Service for managing blacklisted JWT tokens.
    
    Provides secure token invalidation for logout, password changes,
    and other security-critical operations.
    """
    
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.blacklist_prefix = "blacklist:token:"
        self.user_tokens_prefix = "blacklist:user:"
        
    async def blacklist_token(
        self, 
        token_jti: str, 
        user_id: int,
        expires_at: datetime,
        reason: str = "logout"
    ) -> bool:
        """
        Add a token to the blacklist
        
        Args:
            token_jti: Token's unique identifier (jti claim)
            user_id: User ID who owns the token
            expires_at: When the token naturally expires
            reason: Reason for blacklisting (logout, password_change, etc.)
            
        Returns:
            True if successfully blacklisted
        """
        try:
            # Calculate TTL - only store until natural expiration
            now = datetime.utcnow()
            if expires_at <= now:
                # Token already expired, no need to blacklist
                return True
                
            ttl = expires_at - now
            
            # Store blacklist entry
            blacklist_key = f"{self.blacklist_prefix}{token_jti}"
            blacklist_data = {
                "user_id": user_id,
                "blacklisted_at": str(now),
                "expires_at": str(expires_at),
                "reason": reason
            }
            
            await self.cache.set(blacklist_key, blacklist_data, ttl)
            
            # Add to user's blacklisted tokens list
            user_tokens_key = f"{self.user_tokens_prefix}{user_id}"
            user_tokens = await self.cache.get(user_tokens_key) or []
            if token_jti not in user_tokens:
                user_tokens.append(token_jti)
                # Set TTL to longest token expiration for this user
                max_ttl = timedelta(days=get_settings().jwt_refresh_token_expire_days)
                await self.cache.set(user_tokens_key, user_tokens, max_ttl)
            
            return True
            
        except Exception as e:
            print(f"Error blacklisting token {token_jti}: {e}")
            return False
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """
        Check if a token is blacklisted
        
        Args:
            token_jti: Token's unique identifier
            
        Returns:
            True if token is blacklisted
        """
        try:
            blacklist_key = f"{self.blacklist_prefix}{token_jti}"
            return await self.cache.exists(blacklist_key)
        except Exception as e:
            print(f"Error checking token blacklist {token_jti}: {e}")
            # Fail secure - treat errors as blacklisted
            return True
    
    async def blacklist_all_user_tokens(
        self, 
        user_id: int,
        reason: str = "security_action"
    ) -> bool:
        """
        Blacklist all tokens for a user
        
        Used for password changes, account suspension, etc.
        
        Args:
            user_id: User ID whose tokens to blacklist
            reason: Reason for mass blacklisting
            
        Returns:
            True if successful
        """
        try:
            user_tokens_key = f"{self.user_tokens_prefix}{user_id}"
            token_jtis = await self.cache.get(user_tokens_key) or []
            
            # Blacklist each token individually
            now = datetime.utcnow()
            default_expiry = now + timedelta(days=get_settings().jwt_refresh_token_expire_days)
            
            for token_jti in token_jtis:
                await self.blacklist_token(token_jti, user_id, default_expiry, reason)
            
            # Clear the user tokens list
            await self.cache.delete(user_tokens_key)
            
            return True
            
        except Exception as e:
            print(f"Error blacklisting all tokens for user {user_id}: {e}")
            return False
    
    async def get_blacklisted_tokens_count(self, user_id: int) -> int:
        """
        Get count of blacklisted tokens for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of blacklisted tokens
        """
        try:
            user_tokens_key = f"{self.user_tokens_prefix}{user_id}"
            token_jtis = await self.cache.get(user_tokens_key) or []
            return len(token_jtis)
        except Exception:
            return 0
    
    async def cleanup_expired_blacklist_entries(self) -> int:
        """
        Manual cleanup of expired blacklist entries
        
        Redis should handle this automatically with TTL, but this
        provides manual cleanup if needed.
        
        Returns:
            Number of entries cleaned up
        """
        # This would require Redis SCAN operations
        # For now, rely on Redis TTL for automatic cleanup
        return 0


class UserCacheService:
    """
    Service for caching user data and profile information.
    
    Reduces database load by caching frequently accessed user data.
    """
    
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.user_prefix = "user:"
        self.user_profile_prefix = "user:profile:"
        self.user_permissions_prefix = "user:permissions:"
        
    async def cache_user_profile(
        self, 
        user_id: int, 
        profile_data: dict,
        ttl: timedelta = timedelta(hours=1)
    ) -> bool:
        """
        Cache user profile data
        
        Args:
            user_id: User ID
            profile_data: Profile data to cache
            ttl: Time to live for cache entry
            
        Returns:
            True if cached successfully
        """
        try:
            profile_key = f"{self.user_profile_prefix}{user_id}"
            return await self.cache.set(profile_key, profile_data, ttl)
        except Exception as e:
            print(f"Error caching user profile {user_id}: {e}")
            return False
    
    async def get_cached_user_profile(self, user_id: int) -> Optional[dict]:
        """
        Get cached user profile data
        
        Args:
            user_id: User ID
            
        Returns:
            Profile data if cached, None otherwise
        """
        try:
            profile_key = f"{self.user_profile_prefix}{user_id}"
            return await self.cache.get(profile_key)
        except Exception as e:
            print(f"Error getting cached user profile {user_id}: {e}")
            return None
    
    async def invalidate_user_cache(self, user_id: int) -> bool:
        """
        Invalidate all cached data for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if invalidated successfully
        """
        try:
            keys_to_delete = [
                f"{self.user_profile_prefix}{user_id}",
                f"{self.user_permissions_prefix}{user_id}"
            ]
            
            for key in keys_to_delete:
                await self.cache.delete(key)
                
            return True
        except Exception as e:
            print(f"Error invalidating user cache {user_id}: {e}")
            return False
    
    async def cache_user_permissions(
        self, 
        user_id: int, 
        permissions: List[str],
        ttl: timedelta = timedelta(minutes=30)
    ) -> bool:
        """
        Cache user permissions
        
        Args:
            user_id: User ID
            permissions: List of permission strings
            ttl: Time to live for cache entry
            
        Returns:
            True if cached successfully
        """
        try:
            permissions_key = f"{self.user_permissions_prefix}{user_id}"
            return await self.cache.set(permissions_key, permissions, ttl)
        except Exception as e:
            print(f"Error caching user permissions {user_id}: {e}")
            return False
    
    async def get_cached_user_permissions(self, user_id: int) -> Optional[List[str]]:
        """
        Get cached user permissions
        
        Args:
            user_id: User ID
            
        Returns:
            List of permissions if cached, None otherwise
        """
        try:
            permissions_key = f"{self.user_permissions_prefix}{user_id}"
            return await self.cache.get(permissions_key)
        except Exception as e:
            print(f"Error getting cached user permissions {user_id}: {e}")
            return None


# Dependency injection functions
async def get_token_blacklist_service(cache: CacheService) -> TokenBlacklistService:
    """Get token blacklist service instance"""
    return TokenBlacklistService(cache)


async def get_user_cache_service(cache: CacheService) -> UserCacheService:
    """Get user cache service instance"""
    return UserCacheService(cache)