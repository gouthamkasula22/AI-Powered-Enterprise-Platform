"""
Chat Authentication and Authorization Repository Interfaces

This module defines repository interfaces for user-based chat isolation,
role-based access control, and audit logging.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime

from ..entities.chat_auth import (
    ChatUserRole, ThreadAccess, ChatAuditLog, UserChatIsolation,
    ChatPermission, ChatRole, AuditAction, AccessLevel
)


class ChatUserRoleRepository(ABC):
    """Repository interface for chat user roles and permissions."""
    
    @abstractmethod
    async def create(self, role: ChatUserRole) -> ChatUserRole:
        """Create a new user role."""
        pass
    
    @abstractmethod
    async def update(self, role: ChatUserRole) -> ChatUserRole:
        """Update a user role."""
        pass
    
    @abstractmethod
    async def get_by_id(self, role_id: int) -> Optional[ChatUserRole]:
        """Get a role by ID."""
        pass
    
    @abstractmethod
    async def delete(self, role_id: int) -> bool:
        """Delete a role."""
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: int, thread_id: Optional[int] = None) -> List[ChatUserRole]:
        """Get all roles for a user, optionally filtered by thread."""
        pass
    
    @abstractmethod
    async def get_thread_roles(self, thread_id: int) -> List[ChatUserRole]:
        """Get all user roles for a specific thread."""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: int, thread_id: Optional[int] = None) -> Set[ChatPermission]:
        """Get effective permissions for a user in a thread or system-wide."""
        pass
    
    @abstractmethod
    async def has_permission(self, user_id: int, permission: ChatPermission, thread_id: Optional[int] = None) -> bool:
        """Check if user has a specific permission."""
        pass
    
    @abstractmethod
    async def assign_role(
        self, 
        user_id: int, 
        role: ChatRole,
        thread_id: Optional[int] = None,
        granted_by: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> ChatUserRole:
        """Assign a role to a user."""
        pass
    
    @abstractmethod
    async def revoke_role(self, user_id: int, role: ChatRole, thread_id: Optional[int] = None) -> bool:
        """Revoke a role from a user."""
        pass
    
    @abstractmethod
    async def get_users_with_role(self, role: ChatRole, thread_id: Optional[int] = None) -> List[ChatUserRole]:
        """Get all users with a specific role."""
        pass
    
    @abstractmethod
    async def get_expired_roles(self) -> List[ChatUserRole]:
        """Get roles that have expired."""
        pass
    
    @abstractmethod
    async def cleanup_expired_roles(self) -> int:
        """Remove expired roles. Returns count of cleaned up roles."""
        pass


class ThreadAccessRepository(ABC):
    """Repository interface for thread access control."""
    
    @abstractmethod
    async def create(self, access: ThreadAccess) -> ThreadAccess:
        """Create a new thread access rule."""
        pass
    
    @abstractmethod
    async def update(self, access: ThreadAccess) -> ThreadAccess:
        """Update a thread access rule."""
        pass
    
    @abstractmethod
    async def get_by_id(self, access_id: int) -> Optional[ThreadAccess]:
        """Get access rule by ID."""
        pass
    
    @abstractmethod
    async def delete(self, access_id: int) -> bool:
        """Delete an access rule."""
        pass
    
    @abstractmethod
    async def get_thread_access(self, thread_id: int) -> List[ThreadAccess]:
        """Get all access rules for a thread."""
        pass
    
    @abstractmethod
    async def get_user_thread_access(self, user_id: int, thread_id: int) -> Optional[ThreadAccess]:
        """Get specific user's access to a thread."""
        pass
    
    @abstractmethod
    async def check_thread_access(self, user_id: int, thread_id: int, permission: ChatPermission) -> bool:
        """Check if user has specific access to a thread."""
        pass
    
    @abstractmethod
    async def grant_thread_access(
        self,
        thread_id: int,
        user_id: Optional[int],
        access_level: AccessLevel,
        permissions: Set[ChatPermission],
        granted_by: int,
        expires_at: Optional[datetime] = None
    ) -> ThreadAccess:
        """Grant access to a thread."""
        pass
    
    @abstractmethod
    async def revoke_thread_access(self, thread_id: int, user_id: Optional[int] = None) -> bool:
        """Revoke access to a thread."""
        pass
    
    @abstractmethod
    async def get_accessible_threads(self, user_id: int) -> List[int]:
        """Get list of thread IDs accessible to a user."""
        pass
    
    @abstractmethod
    async def get_public_threads(self) -> List[int]:
        """Get list of publicly accessible thread IDs."""
        pass
    
    @abstractmethod
    async def cleanup_expired_access(self) -> int:
        """Remove expired access rules. Returns count of cleaned up rules."""
        pass


class ChatAuditLogRepository(ABC):
    """Repository interface for chat audit logging."""
    
    @abstractmethod
    async def create(self, audit_log: ChatAuditLog) -> ChatAuditLog:
        """Create a new audit log entry."""
        pass
    
    @abstractmethod
    async def log_action(
        self,
        user_id: Optional[int],
        action: AuditAction,
        entity_type: str,
        entity_id: Optional[int] = None,
        thread_id: Optional[int] = None,
        message_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatAuditLog:
        """Log a chat action."""
        pass
    
    @abstractmethod
    async def get_by_id(self, log_id: int) -> Optional[ChatAuditLog]:
        """Get audit log by ID."""
        pass
    
    @abstractmethod
    async def get_user_logs(
        self, 
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ChatAuditLog]:
        """Get audit logs for a specific user."""
        pass
    
    @abstractmethod
    async def get_thread_logs(
        self, 
        thread_id: int,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ChatAuditLog]:
        """Get audit logs for a specific thread."""
        pass
    
    @abstractmethod
    async def get_logs_by_action(
        self, 
        action: AuditAction,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ChatAuditLog]:
        """Get audit logs by action type."""
        pass
    
    @abstractmethod
    async def search_logs(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        actions: Optional[List[AuditAction]] = None,
        user_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatAuditLog]:
        """Search audit logs."""
        pass
    
    @abstractmethod
    async def get_activity_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "action"  # action, user, thread, hour, day
    ) -> Dict[str, Any]:
        """Get activity summary for a time period."""
        pass
    
    @abstractmethod
    async def get_user_activity_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get activity statistics for a user."""
        pass
    
    @abstractmethod
    async def cleanup_old_logs(self, older_than_days: int = 90) -> int:
        """Clean up old audit logs. Returns count of deleted logs."""
        pass


class UserChatIsolationRepository(ABC):
    """Repository interface for user chat isolation."""
    
    @abstractmethod
    async def create(self, isolation: UserChatIsolation) -> UserChatIsolation:
        """Create user isolation settings."""
        pass
    
    @abstractmethod
    async def update(self, isolation: UserChatIsolation) -> UserChatIsolation:
        """Update user isolation settings."""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[UserChatIsolation]:
        """Get isolation settings for a user."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete isolation settings for a user."""
        pass
    
    @abstractmethod
    async def check_thread_access(self, user_id: int, thread_id: int) -> bool:
        """Check if user can access a thread based on isolation settings."""
        pass
    
    @abstractmethod
    async def check_user_interaction(self, user_id: int, other_user_id: int) -> bool:
        """Check if user can interact with another user."""
        pass
    
    @abstractmethod
    async def check_file_upload(self, user_id: int, file_type: str) -> bool:
        """Check if user can upload a specific file type."""
        pass
    
    @abstractmethod
    async def check_thread_limit(self, user_id: int, current_count: int) -> bool:
        """Check if user is within thread creation limit."""
        pass
    
    @abstractmethod
    async def add_blocked_user(self, user_id: int, blocked_user_id: int) -> bool:
        """Add a user to the blocked list."""
        pass
    
    @abstractmethod
    async def remove_blocked_user(self, user_id: int, blocked_user_id: int) -> bool:
        """Remove a user from the blocked list."""
        pass
    
    @abstractmethod
    async def add_allowed_thread(self, user_id: int, thread_id: int) -> bool:
        """Add a thread to the allowed list for strict isolation."""
        pass
    
    @abstractmethod
    async def remove_allowed_thread(self, user_id: int, thread_id: int) -> bool:
        """Remove a thread from the allowed list."""
        pass
    
    @abstractmethod
    async def get_isolated_users(self, isolation_level: str = "strict") -> List[UserChatIsolation]:
        """Get users with specific isolation level."""
        pass


class ChatRateLimitRepository(ABC):
    """Repository interface for chat rate limiting."""
    
    @abstractmethod
    async def check_rate_limit(self, user_id: int, action_type: str) -> Tuple[bool, Optional[datetime]]:
        """Check if user is within rate limit. Returns (allowed, blocked_until)."""
        pass
    
    @abstractmethod
    async def increment_action_count(self, user_id: int, action_type: str) -> int:
        """Increment action count for user. Returns new count."""
        pass
    
    @abstractmethod
    async def get_user_rate_limits(self, user_id: int) -> List[Dict[str, Any]]:
        """Get current rate limit status for user."""
        pass
    
    @abstractmethod
    async def set_rate_limit(
        self, 
        user_id: int, 
        action_type: str,
        limit_per_window: int,
        window_duration_minutes: int = 60
    ) -> bool:
        """Set rate limit for user and action type."""
        pass
    
    @abstractmethod
    async def block_user_temporarily(
        self, 
        user_id: int, 
        action_type: str,
        blocked_until: datetime
    ) -> bool:
        """Temporarily block user for specific action type."""
        pass
    
    @abstractmethod
    async def unblock_user(self, user_id: int, action_type: str) -> bool:
        """Remove block for user and action type."""
        pass
    
    @abstractmethod
    async def cleanup_expired_blocks(self) -> int:
        """Clean up expired blocks. Returns count of cleaned up blocks."""
        pass
    
    @abstractmethod
    async def reset_rate_limits(self, user_id: Optional[int] = None) -> int:
        """Reset rate limits for user or all users. Returns count of reset limits."""
        pass


class ChatSecurityRepository(ABC):
    """Repository interface for combined chat security operations."""
    
    @abstractmethod
    async def check_user_can_access_thread(self, user_id: int, thread_id: int) -> bool:
        """Comprehensive check if user can access thread (permissions + isolation + rate limits)."""
        pass
    
    @abstractmethod
    async def check_user_can_perform_action(
        self, 
        user_id: int, 
        action: ChatPermission,
        thread_id: Optional[int] = None,
        target_user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if user can perform action. Returns (allowed, reason_if_denied)."""
        pass
    
    @abstractmethod
    async def get_user_security_context(self, user_id: int) -> Dict[str, Any]:
        """Get complete security context for user."""
        pass
    
    @abstractmethod
    async def enforce_security_policies(self, user_id: int, action_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce all security policies and return updated context."""
        pass
    
    @abstractmethod
    async def get_security_violations(
        self, 
        start_date: datetime,
        end_date: datetime,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get security violations in time period."""
        pass