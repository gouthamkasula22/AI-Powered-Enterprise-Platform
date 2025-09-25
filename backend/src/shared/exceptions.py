"""
Shared Exception Classes

Common exception classes used across the application.
"""


class DocumentProcessingError(Exception):
    """Exception raised when document processing fails"""
    pass


class ValidationError(Exception):
    """Exception raised when validation fails"""
    pass


class AuthenticationError(Exception):
    """Exception raised when authentication fails"""
    pass


class AuthorizationError(Exception):
    """Exception raised when authorization fails"""
    pass


class DatabaseError(Exception):
    """Exception raised when database operations fail"""
    pass


class CacheError(Exception):
    """Exception raised when cache operations fail"""
    pass


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid"""
    pass


class ProcessingError(Exception):
    """Exception raised when processing operations fail"""
    pass


class AIError(Exception):
    """Exception raised when AI operations fail"""
    pass


class RateLimitError(Exception):
    """Exception raised when rate limits are exceeded"""
    pass


class NotFoundError(Exception):
    """Exception raised when requested resource is not found"""
    pass