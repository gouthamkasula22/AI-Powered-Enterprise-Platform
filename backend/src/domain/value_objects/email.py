"""
Email Value Object

Ensures email validity and provides a consistent interface for email handling
throughout the domain layer. Immutable by design.
"""

import re
from dataclasses import dataclass
from ..exceptions.domain_exceptions import EmailValidationException


@dataclass(frozen=True)
class Email:
    """Email value object with validation"""
    
    value: str
    
    def __post_init__(self):
        """Validate email format on creation"""
        if not self._is_valid_format(self.value):
            raise EmailValidationException(self.value)
        
        # Normalize email to lowercase
        object.__setattr__(self, 'value', self.value.lower().strip())
    
    @staticmethod
    def _is_valid_format(email: str) -> bool:
        """
        Validate email format using RFC 5322 compliant regex
        
        Args:
            email: Email string to validate
            
        Returns:
            bool: True if valid format, False otherwise
        """
        if not email or len(email) > 254:  # RFC 5321 limit
            return False
        
        # Basic RFC 5322 compliant regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # Additional checks
        local, domain = email.rsplit('@', 1)
        
        # Local part length check (RFC 5321)
        if len(local) > 64:
            return False
        
        # Domain part checks
        if len(domain) > 253:
            return False
        
        return True
    
    @property
    def local_part(self) -> str:
        """Get the local part of the email (before @)"""
        return self.value.split('@')[0]
    
    @property
    def domain_part(self) -> str:
        """Get the domain part of the email (after @)"""
        return self.value.split('@')[1]
    
    def __str__(self) -> str:
        return self.value