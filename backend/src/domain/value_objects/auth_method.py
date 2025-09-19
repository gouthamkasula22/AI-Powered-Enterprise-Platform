"""
Authentication Method Value Object

Represents the method used for user authentication (password, OAuth, etc.)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from ..exceptions.domain_exceptions import ValidationError


class AuthMethodType(Enum):
    """Supported authentication methods"""
    PASSWORD = "password"
    GOOGLE_OAUTH = "google_oauth"
    GITHUB_OAUTH = "github_oauth"
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AuthMethod:
    """Authentication method value object"""
    
    method_type: AuthMethodType
    provider_id: Optional[str] = None  # For OAuth providers, stores the provider user ID
    
    def __post_init__(self):
        """Validate authentication method"""
        if self.method_type in [AuthMethodType.GOOGLE_OAUTH, AuthMethodType.GITHUB_OAUTH]:
            if not self.provider_id:
                raise ValidationError(f"OAuth method {self.method_type} requires provider_id")
    
    @classmethod
    def password(cls) -> "AuthMethod":
        """Create password authentication method"""
        return cls(method_type=AuthMethodType.PASSWORD)
    
    @classmethod
    def google_oauth(cls, provider_id: str) -> "AuthMethod":
        """Create Google OAuth authentication method"""
        return cls(method_type=AuthMethodType.GOOGLE_OAUTH, provider_id=provider_id)
    
    @classmethod
    def github_oauth(cls, provider_id: str) -> "AuthMethod":
        """Create GitHub OAuth authentication method"""
        return cls(method_type=AuthMethodType.GITHUB_OAUTH, provider_id=provider_id)
    
    def is_oauth(self) -> bool:
        """Check if this is an OAuth authentication method"""
        return self.method_type in [AuthMethodType.GOOGLE_OAUTH, AuthMethodType.GITHUB_OAUTH]
    
    def is_password(self) -> bool:
        """Check if this is a password authentication method"""
        return self.method_type == AuthMethodType.PASSWORD
    
    def __str__(self) -> str:
        if self.provider_id:
            return f"{self.method_type}:{self.provider_id}"
        return str(self.method_type)