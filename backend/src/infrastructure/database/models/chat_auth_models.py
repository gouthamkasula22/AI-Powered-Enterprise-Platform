"""
Chat Authentication and Authorization Database Models

This module defines database models for user-based chat isolation,
role-based access control, and audit logging.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, BigInteger, Boolean, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum

from ..config import Base

if TYPE_CHECKING:
    from .chat_models import ChatThread, ChatMessage
    from .user_model import UserModel


class ChatPermissionType(Enum):
    """Database enum for chat permissions."""
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


class ChatRoleType(Enum):
    """Database enum for chat roles."""
    VIEWER = "viewer"
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"


class AuditActionType(Enum):
    """Database enum for audit actions."""
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


class AccessLevelType(Enum):
    """Database enum for access levels."""
    PRIVATE = "private"
    SHARED_READ = "shared_read"
    SHARED_WRITE = "shared_write"
    PUBLIC_READ = "public_read"
    PUBLIC_WRITE = "public_write"


class ChatUserRole(Base):
    """Model for user roles and permissions in the chat system."""
    __tablename__ = "chat_user_roles"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    thread_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=True)
    granted_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Role and permissions
    role: Mapped[str] = mapped_column(String(20))
    permissions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Timestamps and status
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id])
    thread = relationship("ChatThread", foreign_keys=[thread_id])
    granter = relationship("UserModel", foreign_keys=[granted_by])
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_chat_user_roles_user_id", "user_id"),
        Index("idx_chat_user_roles_thread_id", "thread_id"),
        Index("idx_chat_user_roles_role", "role"),
        Index("idx_chat_user_roles_active", "is_active", "expires_at"),
        Index("idx_chat_user_roles_user_thread", "user_id", "thread_id"),
    )


class ThreadAccess(Base):
    """Model for thread access control."""
    __tablename__ = "thread_access"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    thread_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_threads.id", ondelete="CASCADE"))
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    granted_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Access control
    access_level: Mapped[str] = mapped_column(String(20))
    permissions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    thread = relationship("ChatThread")
    user = relationship("UserModel", foreign_keys=[user_id])
    granter = relationship("UserModel", foreign_keys=[granted_by])
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_thread_access_thread_id", "thread_id"),
        Index("idx_thread_access_user_id", "user_id"),
        Index("idx_thread_access_level", "access_level"),
        Index("idx_thread_access_expires", "expires_at"),
        Index("idx_thread_access_thread_user", "thread_id", "user_id"),
    )


class ChatAuditLog(Base):
    """Model for chat activity audit logging."""
    __tablename__ = "chat_audit_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    thread_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chat_threads.id", ondelete="SET NULL"), nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True)
    
    # Action details
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Change tracking
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Additional metadata
    additional_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id])
    thread = relationship("ChatThread", foreign_keys=[thread_id])
    message = relationship("ChatMessage", foreign_keys=[message_id])
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_chat_audit_logs_user_id", "user_id"),
        Index("idx_chat_audit_logs_thread_id", "thread_id"),
        Index("idx_chat_audit_logs_message_id", "message_id"),
        Index("idx_chat_audit_logs_action", "action"),
        Index("idx_chat_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_chat_audit_logs_created_at", "created_at"),
        Index("idx_chat_audit_logs_user_action", "user_id", "action", "created_at"),
        Index("idx_chat_audit_logs_session", "session_id"),
    )


class UserChatIsolation(Base):
    """Model for user chat isolation settings."""
    __tablename__ = "user_chat_isolation"
    
    # Primary key (also foreign key)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Isolation settings
    isolation_level: Mapped[str] = mapped_column(String(20), default="standard")
    allowed_thread_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=list)
    blocked_user_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=list)
    content_filters: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Limits
    max_threads: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_messages_per_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allowed_file_types: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # Additional restrictions
    restrictions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="chat_isolation")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_chat_isolation_level", "isolation_level"),
        Index("idx_user_chat_isolation_updated", "updated_at"),
        Index("idx_user_chat_isolation_blocked_users", "blocked_user_ids", postgresql_using="gin"),
        Index("idx_user_chat_isolation_allowed_threads", "allowed_thread_ids", postgresql_using="gin"),
    )


class ChatRateLimit(Base):
    """Model for tracking user rate limits in chat."""
    __tablename__ = "chat_rate_limits"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Rate limiting
    action_type: Mapped[str] = mapped_column(String(50))  # message_send, thread_create, etc.
    count: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    window_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    limit_per_window: Mapped[int] = mapped_column(Integer)
    
    # Status
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_chat_rate_limits_user_action", "user_id", "action_type"),
        Index("idx_chat_rate_limits_window", "window_start", "window_duration_minutes"),
        Index("idx_chat_rate_limits_blocked", "is_blocked", "blocked_until"),
        Index("idx_chat_rate_limits_updated", "updated_at"),
    )