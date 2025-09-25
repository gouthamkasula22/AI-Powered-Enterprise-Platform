"""
Chat Authentication and Authorization Entities

This module contains entities for user-based chat isolation, role-based access control,
and comprehensive audit logging for the chat system.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from enum import Enum


class ChatPermission(Enum):
    """Permissions for chat operations."""
    READ_THREAD = "read_thread"
    WRITE_MESSAGE = "write_message"
    EDIT_MESSAGE = "edit_message"
    DELETE_MESSAGE = "delete_message"
    REACT_TO_MESSAGE = "react_to_message"
    CREATE_THREAD = "create_thread"
    DELETE_THREAD = "delete_thread"
    SHARE_THREAD = "share_thread"
    MODERATE_THREAD = "moderate_thread"
    UPLOAD_DOCUMENT = "upload_document"
    DELETE_DOCUMENT = "delete_document"
    ADMIN_ACCESS = "admin_access"


class ChatRole(Enum):
    """Roles for chat access control."""
    VIEWER = "viewer"
    PARTICIPANT = "participant"  
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"


class AuditAction(Enum):
    """Types of actions for audit logging."""
    THREAD_CREATED = "thread_created"
    THREAD_UPDATED = "thread_updated"
    THREAD_DELETED = "thread_deleted"
    THREAD_SHARED = "thread_shared"
    THREAD_ARCHIVED = "thread_archived"
    MESSAGE_SENT = "message_sent"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_REACTED = "message_reacted"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    USER_PERMISSION_CHANGED = "user_permission_changed"
    USER_ROLE_CHANGED = "user_role_changed"
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    SEARCH_PERFORMED = "search_performed"


class AccessLevel(Enum):
    """Access levels for thread sharing."""
    PRIVATE = "private"
    SHARED_READ = "shared_read"
    SHARED_WRITE = "shared_write"
    PUBLIC_READ = "public_read"
    PUBLIC_WRITE = "public_write"


@dataclass(frozen=True)
class ChatUserRole:
    """Represents a user's role and permissions in the chat system."""
    id: int
    user_id: int
    thread_id: Optional[int] = None  # None means system-wide role
    role: ChatRole = ChatRole.PARTICIPANT
    permissions: Set[ChatPermission] = field(default_factory=set)
    granted_by: Optional[int] = None
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    def has_permission(self, permission: ChatPermission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions or ChatPermission.ADMIN_ACCESS in self.permissions
    
    def can_read_thread(self) -> bool:
        """Check if user can read threads."""
        return self.has_permission(ChatPermission.READ_THREAD)
    
    def can_write_messages(self) -> bool:
        """Check if user can write messages."""
        return self.has_permission(ChatPermission.WRITE_MESSAGE)
    
    def can_moderate(self) -> bool:
        """Check if user can moderate content."""
        return self.has_permission(ChatPermission.MODERATE_THREAD)
    
    def is_admin(self) -> bool:
        """Check if user has admin access."""
        return self.has_permission(ChatPermission.ADMIN_ACCESS)
    
    def is_expired(self) -> bool:
        """Check if role has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if role is valid and active."""
        return self.is_active and not self.is_expired()


@dataclass(frozen=True)
class ThreadAccess:
    """Represents access control for a thread."""
    id: int
    thread_id: int
    user_id: Optional[int] = None  # None means applies to all users
    access_level: AccessLevel = AccessLevel.PRIVATE
    permissions: Set[ChatPermission] = field(default_factory=set)
    granted_by: int = 0
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)  # Additional access conditions
    
    def is_public_access(self) -> bool:
        """Check if this grants public access."""
        return self.access_level in [AccessLevel.PUBLIC_READ, AccessLevel.PUBLIC_WRITE]
    
    def allows_writing(self) -> bool:
        """Check if access allows writing."""
        return self.access_level in [AccessLevel.SHARED_WRITE, AccessLevel.PUBLIC_WRITE]
    
    def allows_reading(self) -> bool:
        """Check if access allows reading."""
        return self.access_level != AccessLevel.PRIVATE
    
    def is_expired(self) -> bool:
        """Check if access has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def check_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if additional conditions are met."""
        # Can be extended to check IP restrictions, time-based access, etc.
        return True


@dataclass(frozen=True)
class ChatAuditLog:
    """Represents an audit log entry for chat activities."""
    id: int
    user_id: Optional[int]
    thread_id: Optional[int] = None
    message_id: Optional[int] = None
    action: AuditAction = AuditAction.THREAD_CREATED
    entity_type: str = "thread"
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the action."""
        action_descriptions = {
            AuditAction.THREAD_CREATED: "Created thread",
            AuditAction.MESSAGE_SENT: "Sent message", 
            AuditAction.MESSAGE_EDITED: "Edited message",
            AuditAction.DOCUMENT_UPLOADED: "Uploaded document",
            AuditAction.USER_ROLE_CHANGED: "Changed user role"
        }
        
        base = action_descriptions.get(self.action, str(self.action.value))
        if self.entity_id:
            return f"{base} #{self.entity_id}"
        return base
    
    def involves_user(self, user_id: int) -> bool:
        """Check if audit log involves a specific user."""
        return self.user_id == user_id
    
    def involves_thread(self, thread_id: int) -> bool:
        """Check if audit log involves a specific thread."""
        return self.thread_id == thread_id
    
    def get_change_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of what changed."""
        if not self.old_values or not self.new_values:
            return None
            
        changes = {}
        for key in self.new_values:
            old_val = self.old_values.get(key)
            new_val = self.new_values[key]
            if old_val != new_val:
                changes[key] = {
                    "from": old_val,
                    "to": new_val
                }
        
        return changes if changes else None


@dataclass(frozen=True)  
class UserChatIsolation:
    """Represents user isolation settings and context."""
    user_id: int
    isolation_level: str = "standard"  # standard, strict, custom
    allowed_thread_ids: Set[int] = field(default_factory=set)
    blocked_user_ids: Set[int] = field(default_factory=set)
    content_filters: List[str] = field(default_factory=list)
    max_threads: Optional[int] = None
    max_messages_per_hour: Optional[int] = None
    allowed_file_types: Set[str] = field(default_factory=set)
    restrictions: Dict[str, Any] = field(default_factory=dict)
    
    def can_access_thread(self, thread_id: int) -> bool:
        """Check if user can access a specific thread."""
        if self.isolation_level == "strict":
            return thread_id in self.allowed_thread_ids
        return True  # Standard isolation allows all threads by default
    
    def can_interact_with_user(self, other_user_id: int) -> bool:
        """Check if user can interact with another user."""
        return other_user_id not in self.blocked_user_ids
    
    def can_upload_file_type(self, file_type: str) -> bool:
        """Check if user can upload a specific file type."""
        if not self.allowed_file_types:
            return True  # No restrictions if empty
        return file_type.lower() in {t.lower() for t in self.allowed_file_types}
    
    def is_within_thread_limit(self, current_thread_count: int) -> bool:
        """Check if user is within thread creation limit."""
        if not self.max_threads:
            return True
        return current_thread_count < self.max_threads
    
    def get_active_restrictions(self) -> List[str]:
        """Get list of active restrictions for the user."""
        restrictions = []
        
        if self.isolation_level == "strict":
            restrictions.append("Limited to specific threads")
            
        if self.blocked_user_ids:
            restrictions.append(f"Blocked from {len(self.blocked_user_ids)} users")
            
        if self.max_threads:
            restrictions.append(f"Maximum {self.max_threads} threads")
            
        if self.max_messages_per_hour:
            restrictions.append(f"Maximum {self.max_messages_per_hour} messages/hour")
            
        if self.allowed_file_types:
            restrictions.append(f"File uploads limited to: {', '.join(self.allowed_file_types)}")
            
        return restrictions


# Default role permission mappings
ROLE_PERMISSIONS = {
    ChatRole.VIEWER: {
        ChatPermission.READ_THREAD,
    },
    ChatRole.PARTICIPANT: {
        ChatPermission.READ_THREAD,
        ChatPermission.WRITE_MESSAGE,
        ChatPermission.REACT_TO_MESSAGE,
        ChatPermission.UPLOAD_DOCUMENT,
    },
    ChatRole.MODERATOR: {
        ChatPermission.READ_THREAD,
        ChatPermission.WRITE_MESSAGE,
        ChatPermission.EDIT_MESSAGE,
        ChatPermission.DELETE_MESSAGE,
        ChatPermission.REACT_TO_MESSAGE,
        ChatPermission.CREATE_THREAD,
        ChatPermission.SHARE_THREAD,
        ChatPermission.MODERATE_THREAD,
        ChatPermission.UPLOAD_DOCUMENT,
        ChatPermission.DELETE_DOCUMENT,
    },
    ChatRole.ADMIN: {
        ChatPermission.READ_THREAD,
        ChatPermission.WRITE_MESSAGE,
        ChatPermission.EDIT_MESSAGE,
        ChatPermission.DELETE_MESSAGE,
        ChatPermission.REACT_TO_MESSAGE,
        ChatPermission.CREATE_THREAD,
        ChatPermission.DELETE_THREAD,
        ChatPermission.SHARE_THREAD,
        ChatPermission.MODERATE_THREAD,
        ChatPermission.UPLOAD_DOCUMENT,
        ChatPermission.DELETE_DOCUMENT,
        ChatPermission.ADMIN_ACCESS,
    },
    ChatRole.OWNER: {
        ChatPermission.READ_THREAD,
        ChatPermission.WRITE_MESSAGE,
        ChatPermission.EDIT_MESSAGE,
        ChatPermission.DELETE_MESSAGE,
        ChatPermission.REACT_TO_MESSAGE,
        ChatPermission.CREATE_THREAD,
        ChatPermission.DELETE_THREAD,
        ChatPermission.SHARE_THREAD,
        ChatPermission.MODERATE_THREAD,
        ChatPermission.UPLOAD_DOCUMENT,
        ChatPermission.DELETE_DOCUMENT,
        ChatPermission.ADMIN_ACCESS,
    }
}