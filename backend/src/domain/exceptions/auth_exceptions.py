"""
Authentication-specific exceptions.

Contains exceptions related to authentication failures like
token blacklisting, invalid credentials, etc.
"""

from .domain_exceptions import DomainException


class TokenBlacklistedException(DomainException):
    """Exception raised when a token has been blacklisted"""
    error_code = "TOKEN_BLACKLISTED"
    status_code = 401
    
    def __init__(self, message: str = "Token has been blacklisted or revoked"):
        super().__init__(message)