"""
Login History (Audit) Model

This module defines the LoginHistory model for tracking user login attempts,
security events, and audit trails for compli    # Relationships - Temporarily commented out for M1.2 validation
    # user: Mapped["User"] = relationship(
    #     "User",
    #     back_populates="login_history",
    #     lazy="select"
    # )
    #
    # session: Mapped[Optional["UserSession"]] = relationship(
    #     "UserSession",
    #     lazy="select"
    # )curity monitoring.

Author: User Authentication System
Version: 1.0.0
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float, Enum, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .user import User
    from .session import UserSession


class LoginHistory(BaseModel):
    """
    Login history model for security audit trails.
    
    This model tracks all login attempts, successful or failed, along with
    security metadata for monitoring and compliance purposes.
    """
    __tablename__ = 'login_history'
    
    # Foreign keys
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="Reference to the user (null for failed attempts with invalid user)"
    )
    
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('user_sessions.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        doc="Reference to the created session (null for failed attempts)"
    )
    
    # Login attempt details
    login_type: Mapped[str] = mapped_column(
        Enum('password', 'social_google', 'social_facebook', 'social_linkedin', 'mfa', 'token_refresh', name='login_type_enum'),
        nullable=False,
        index=True,
        doc="Type of login attempt"
    )
    
    result: Mapped[str] = mapped_column(
        Enum('success', 'failed_password', 'failed_user_not_found', 'failed_account_locked', 'failed_account_disabled', 'failed_mfa', 'failed_rate_limit', name='login_result_enum'),
        nullable=False,
        index=True,
        doc="Result of the login attempt"
    )
    
    # Identification fields
    email_attempted: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Email address used in login attempt"
    )
    
    username_attempted: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Username used in login attempt"
    )
    
    # Network and device information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,
        doc="IP address of the login attempt"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string from the client"
    )
    
    device_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Device fingerprint for tracking"
    )
    
    # Geographic information
    country: Mapped[Optional[str]] = mapped_column(
        String(2),  # ISO country code
        nullable=True,
        index=True,
        doc="Country code from IP geolocation"
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="City from IP geolocation"
    )
    
    # Security analysis
    risk_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Risk score (0-1) calculated for this attempt"
    )
    
    is_suspicious: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this attempt was flagged as suspicious"
    )
    
    # Failure details
    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed reason for login failure"
    )
    
    # MFA details
    mfa_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="MFA method used (if applicable)"
    )
    
    mfa_successful: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        doc="Whether MFA was successful (if used)"
    )
    
    # Metadata
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Duration of login attempt in milliseconds"
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="select"
    )
    
    session: Mapped[Optional["UserSession"]] = relationship(
        "UserSession",
        lazy="select"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Ensure risk score is between 0 and 1
        CheckConstraint(
            'risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1)',
            name='valid_risk_score'
        ),
        # Ensure duration is positive
        CheckConstraint(
            'duration_ms IS NULL OR duration_ms >= 0',
            name='positive_duration'
        ),
        # Composite indexes for common queries
        Index('idx_login_user_result', 'user_id', 'result'),
        Index('idx_login_ip_time', 'ip_address', 'created_at'),
        Index('idx_login_email_result', 'email_attempted', 'result'),
        Index('idx_login_suspicious', 'is_suspicious', 'created_at'),
        Index('idx_login_type_result', 'login_type', 'result'),
        Index('idx_login_time_result', 'created_at', 'result'),
    )
    
    @property
    def was_successful(self) -> bool:
        """Check if the login attempt was successful."""
        return self.result == 'success'
    
    @property
    def location_string(self) -> str:
        """Get a formatted location string."""
        if self.city and self.country:
            return f"{self.city}, {self.country}"
        elif self.country:
            return self.country
        else:
            return "Unknown"
    
    def calculate_risk_score(self) -> float:
        """
        Calculate a risk score for this login attempt.
        
        Returns:
            float: Risk score between 0 and 1
        """
        score = 0.0
        
        # Failed attempts increase risk
        if not self.was_successful:
            score += 0.3
        
        # Suspicious flag increases risk
        if self.is_suspicious:
            score += 0.4
        
        # Unknown location increases risk slightly
        if not self.country:
            score += 0.1
        
        # Failed MFA increases risk
        if self.mfa_successful is False:
            score += 0.2
        
        return min(1.0, score)
    
    def mark_suspicious(self, reason: str = None) -> None:
        """Mark this login attempt as suspicious."""
        self.is_suspicious = True
        if reason and not self.failure_reason:
            self.failure_reason = reason
        # Recalculate risk score
        self.risk_score = self.calculate_risk_score()
    
    @classmethod
    def create_attempt(
        cls,
        login_type: str,
        result: str,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        email_attempted: Optional[str] = None,
        username_attempted: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ) -> 'LoginHistory':
        """
        Create a new login history entry.
        
        Args:
            login_type (str): Type of login attempt
            result (str): Result of the attempt
            user_id (uuid.UUID, optional): User ID if successful
            session_id (uuid.UUID, optional): Session ID if successful
            email_attempted (str, optional): Email used in attempt
            username_attempted (str, optional): Username used in attempt
            ip_address (str, optional): IP address
            user_agent (str, optional): User agent
            **kwargs: Additional fields
            
        Returns:
            LoginHistory: New login history entry
        """
        entry = cls(
            user_id=user_id,
            session_id=session_id,
            login_type=login_type,
            result=result,
            email_attempted=email_attempted,
            username_attempted=username_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
        
        # Calculate initial risk score
        entry.risk_score = entry.calculate_risk_score()
        
        return entry
    
    def __repr__(self) -> str:
        """String representation of LoginHistory."""
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, result={self.result}, ip={self.ip_address})>"
