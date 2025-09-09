"""
User Session Model

This module defines the UserSession model for managing user authentication sessions,
including session tokens, device tracking, and security features.

Author: User Authentication System
Version: 1.0.0
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, Integer, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .user import User


class UserSession(BaseModel):
    """
    User session model for managing authentication sessions.
    
    This model tracks active user sessions, including session tokens,
    device information, and security metadata.
    """
    __tablename__ = 'user_sessions'
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Reference to the user who owns this session"
    )
    
    # Session identification
    session_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique session token for authentication"
    )
    
    refresh_token: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Refresh token for extending session"
    )
    
    # Session lifecycle
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the session expires"
    )
    
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Last time this session was used"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the session is currently active"
    )
    
    # Device and location information
    device_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Unique device fingerprint for security"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string from the client"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,
        doc="IP address when session was created"
    )
    
    # Security features
    is_mfa_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether MFA was verified for this session"
    )
    
    mfa_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When MFA was last verified"
    )
    
    # Session metadata
    login_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='password',
        doc="Method used to authenticate (password, social, etc.)"
    )
    
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the session was revoked"
    )
    
    # Relationship - Unidirectional for M1.2 (no back_populates)
    user: Mapped["User"] = relationship(
        "User", 
        lazy="select"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Ensure IP address format if provided
        CheckConstraint(
            r"ip_address IS NULL OR ip_address ~ '^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'",
            name='valid_ip_format'
        ),
        # Composite indexes for common queries
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_token_active', 'session_token', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_ip_time', 'ip_address', 'created_at'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def time_until_expiry(self) -> timedelta:
        """Get time remaining until session expires."""
        return self.expires_at - datetime.utcnow()
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    def extend_session(self, hours: int = 24) -> None:
        """Extend the session expiry time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_accessed = datetime.utcnow()
    
    def revoke(self) -> None:
        """Revoke this session."""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
    
    def update_access(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.utcnow()
    
    def verify_mfa(self) -> None:
        """Mark MFA as verified for this session."""
        self.is_mfa_verified = True
        self.mfa_verified_at = datetime.utcnow()
    
    def requires_mfa_reverification(self, hours: int = 24) -> bool:
        """Check if MFA needs to be re-verified."""
        if not self.is_mfa_verified or not self.mfa_verified_at:
            return True
        
        reverify_time = self.mfa_verified_at + timedelta(hours=hours)
        return datetime.utcnow() > reverify_time
    
    def __repr__(self) -> str:
        """String representation of UserSession."""
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
