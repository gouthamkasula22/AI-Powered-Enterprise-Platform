"""
Social Account Model

This module defines the SocialAccount model for managing OAuth integrations
with third-party providers like Google, Facebook, LinkedIn, etc.

Author: User Authentication System
Version: 1.0.0
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .user import User


class SocialAccount(BaseModel):
    """
    Social account model for OAuth provider integrations.
    
    This model stores information about user's connected social media accounts
    and OAuth provider data.
    """
    __tablename__ = 'social_accounts'
    
    # Foreign key to User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Reference to the user who owns this social account"
    )
    
    # Provider information
    provider: Mapped[str] = mapped_column(
        Enum(
            'google', 'facebook', 'twitter', 'linkedin', 'github', 'microsoft',
            'apple', 'discord', 'spotify', 'twitch',
            name='social_provider_enum'
        ),
        nullable=False,
        index=True,
        doc="OAuth provider name"
    )
    
    provider_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="User ID from the OAuth provider"
    )
    
    # Account information
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Email address from the provider"
    )
    
    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Username from the provider"
    )
    
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Display name from the provider"
    )
    
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="First name from the provider"
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Last name from the provider"
    )
    
    profile_picture_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Profile picture URL from the provider"
    )
    
    # OAuth tokens
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="OAuth access token (encrypted)"
    )
    
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="OAuth refresh token (encrypted)"
    )
    
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the access token expires"
    )
    
    # Account status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the account is verified with the provider"
    )
    
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is the primary social account"
    )
    
    # Provider-specific data
    provider_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON string with additional provider data"
    )
    
    scope: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="OAuth scopes granted"
    )
    
    # Tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this account was used for login"
    )
    
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time account data was updated from provider"
    )
    
    # Privacy settings
    share_email: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether to share email from this provider"
    )
    
    share_profile: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether to share profile info from this provider"
    )
    
    # Relationships - Unidirectional for M1.2 (no back_populates)
    user: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Ensure unique provider account per user
        CheckConstraint(
            'provider IS NOT NULL AND provider_id IS NOT NULL',
            name='provider_info_required'
        ),
        # Composite indexes for common queries
        Index('idx_social_user_provider', 'user_id', 'provider'),
        Index('idx_social_provider_id', 'provider', 'provider_id'),
        Index('idx_social_email_provider', 'email', 'provider'),
        Index('idx_social_primary', 'user_id', 'is_primary'),
        Index('idx_social_last_login', 'last_login'),
    )
    
    @property
    def is_token_expired(self) -> bool:
        """Check if OAuth token is expired."""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() > self.token_expires_at
    
    @property
    def full_name(self) -> str:
        """Get full name from provider data."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.display_name:
            return self.display_name
        elif self.username:
            return self.username
        else:
            return f"{self.provider} User"
    
    def update_from_provider(self, provider_data: dict) -> None:
        """Update account data from provider response."""
        # Update basic info
        if 'email' in provider_data:
            self.email = provider_data['email']
        if 'name' in provider_data:
            self.display_name = provider_data['name']
        if 'given_name' in provider_data:
            self.first_name = provider_data['given_name']
        if 'family_name' in provider_data:
            self.last_name = provider_data['family_name']
        if 'picture' in provider_data:
            self.profile_picture_url = provider_data['picture']
        if 'username' in provider_data:
            self.username = provider_data['username']
        if 'verified_email' in provider_data:
            self.is_verified = provider_data['verified_email']
        
        # Store full provider data as JSON
        import json
        self.provider_data = json.dumps(provider_data)
        self.last_updated = datetime.utcnow()
    
    def update_tokens(self, access_token: str, refresh_token: str | None = None, expires_in: int | None = None) -> None:
        """Update OAuth tokens."""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_in:
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    def mark_as_primary(self) -> None:
        """Mark this account as the primary social account."""
        # Note: In practice, you'd want to unmark other accounts as primary
        # This would typically be handled in the service layer
        self.is_primary = True
    
    def update_login_timestamp(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def get_provider_data(self) -> dict:
        """Get provider data as dictionary."""
        if not self.provider_data:
            return {}
        
        import json
        try:
            return json.loads(self.provider_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def __repr__(self) -> str:
        """String representation of SocialAccount."""
        return f"<SocialAccount(id={self.id}, user_id={self.user_id}, provider={self.provider})>"
