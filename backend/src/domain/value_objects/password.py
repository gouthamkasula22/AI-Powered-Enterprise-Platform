"""
Password Value Object

Handles password validation, hashing, and verification.
Ensures password security requirements are met.
"""

import re
import secrets
import string
from dataclasses import dataclass
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from ..exceptions.domain_exceptions import PasswordValidationException


@dataclass(frozen=True)
class Password:
    """Password value object with validation and hashing"""
    
    value: str
    
    def __post_init__(self):
        """Validate password on creation"""
        if not self._meets_requirements(self.value):
            raise PasswordValidationException(self._get_requirements_message())
    
    @staticmethod
    def _meets_requirements(password: str) -> bool:
        """
        Check if password meets security requirements
        
        Requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter  
        - Contains at least one digit
        - Contains at least one special character
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if meets requirements, False otherwise
        """
        if len(password) < 8:
            return False
        
        if not re.search(r'[A-Z]', password):  # Uppercase
            return False
        
        if not re.search(r'[a-z]', password):  # Lowercase
            return False
        
        if not re.search(r'\d', password):     # Digit
            return False
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Special char
            return False
        
        return True
    
    @staticmethod
    def _get_requirements_message() -> str:
        """Get password requirements message"""
        return (
            "Password must be at least 8 characters long and contain: "
            "uppercase letter, lowercase letter, digit, and special character"
        )
    
    def hash(self) -> str:
        """
        Hash the password using Argon2
        
        Returns:
            str: Hashed password
        """
        ph = PasswordHasher()
        return ph.hash(self.value)
    
    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            hashed_password: Previously hashed password
            plain_password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            ph = PasswordHasher()
            ph.verify(hashed_password, plain_password)
            return True
        except VerifyMismatchError:
            return False
    
    @staticmethod
    def generate_strong_password(length: int = 12) -> str:
        """
        Generate a cryptographically strong password
        
        Args:
            length: Length of password to generate (minimum 8)
            
        Returns:
            str: Generated password
        """
        if length < 8:
            length = 8
        
        # Ensure at least one character from each required category
        uppercase = secrets.choice(string.ascii_uppercase)
        lowercase = secrets.choice(string.ascii_lowercase)
        digit = secrets.choice(string.digits)
        special = secrets.choice('!@#$%^&*(),.?":{}|<>')
        
        # Fill remaining length with random characters
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*(),.?":{}|<>'
        remaining = ''.join(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Combine and shuffle
        password_chars = list(uppercase + lowercase + digit + special + remaining)
        secrets.SystemRandom().shuffle(password_chars)
        
        return ''.join(password_chars)