"""
SQLAlchemy Database Models

Database table definitions that map to domain entities.
These models handle the persistence layer for our domain objects.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from ..config import Base


class UserModel(Base):
    """
    SQLAlchemy model for the users table.
    
    This model maps to the existing users table in the database,
    preserving the current schema and data.
    """
    __tablename__ = 'users'
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    auth_method = Column(String(50), nullable=False, default='PASSWORD')
    auth_provider_id = Column(String(255), nullable=True)
    
    # Optional username
    username = Column(String(50), unique=True, nullable=True, index=True)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(100), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Preferences
    timezone = Column(String(50), default="UTC", nullable=False)
    locale = Column(String(10), default="en", nullable=False)
    
    # Token fields for verification and reset
    email_verification_token = Column(String(255), nullable=True, index=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True, index=True)
    password_reset_expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    chat_isolation = relationship("UserChatIsolation", back_populates="user", uselist=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
        Index('idx_user_verification_token', 'email_verification_token'),
        Index('idx_user_reset_token', 'password_reset_token'),
        Index('idx_user_created_at', 'created_at'),
    )


class OAuthAccountModel(Base):
    """
    OAuth account model for social authentication
    
    Stores information about linked social media accounts.
    """
    __tablename__ = "oauth_accounts"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Link to user
    user_id = Column(Integer, nullable=False, index=True)
    
    # OAuth provider information
    provider = Column(String(50), nullable=False)  # google, facebook, linkedin, etc.
    provider_user_id = Column(String(255), nullable=False)  # ID from the provider
    provider_username = Column(String(100), nullable=True)  # Username from provider
    
    # OAuth tokens (encrypted in production)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Provider profile data
    provider_email = Column(String(255), nullable=True)
    provider_name = Column(String(200), nullable=True)
    provider_picture_url = Column(String(500), nullable=True)
    
    # Metadata
    raw_data = Column(Text, nullable=True)  # JSON string of full provider response
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_oauth_user_provider', 'user_id', 'provider'),
        Index('idx_oauth_provider_user_id', 'provider', 'provider_user_id'),
        Index('idx_oauth_provider_email', 'provider', 'provider_email'),
    )
    
    def __repr__(self):
        return f"<OAuthAccountModel(id={self.id}, user_id={self.user_id}, provider='{self.provider}')>"


class SessionModel(Base):
    """
    User session model for tracking active sessions
    
    Stores session information for security and audit purposes.
    """
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Link to user
    user_id = Column(Integer, nullable=False, index=True)
    
    # Session identification
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=True, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_token_active', 'session_token', 'is_active'),
        Index('idx_session_expires_at', 'expires_at'),
        Index('idx_session_last_activity', 'last_activity_at'),
    )
    
    def __repr__(self):
        return f"<SessionModel(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class AuditLogModel(Base):
    """
    Audit log model for tracking user actions
    
    Stores security-relevant events for compliance and monitoring.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User information
    user_id = Column(Integer, nullable=True, index=True)  # Nullable for anonymous events
    email = Column(String(255), nullable=True, index=True)  # For correlation
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, profile_update, etc.
    event_category = Column(String(30), nullable=False, index=True)  # auth, profile, admin, etc.
    event_description = Column(Text, nullable=True)
    
    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Event metadata
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    additional_data = Column(Text, nullable=True)  # JSON string for extra context
    
    # Timestamp
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_event', 'user_id', 'event_type'),
        Index('idx_audit_event_time', 'event_type', 'created_at'),
        Index('idx_audit_email_event', 'email', 'event_type'),
        Index('idx_audit_category_time', 'event_category', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLogModel(id={self.id}, user_id={self.user_id}, event='{self.event_type}')>"