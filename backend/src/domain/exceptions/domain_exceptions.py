"""
Domain Exceptions - Business Rule Violations

All domain exceptions inherit from DomainException to maintain consistency
and proper error handling throughout the application.
"""

class DomainException(Exception):
    """Base exception for all domain-related errors"""
    
    def __init__(self, message: str, error_code: str = "DOMAIN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationError(DomainException):
    """Raised when domain validation fails"""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class UserNotFoundException(DomainException):
    """Raised when a user cannot be found"""
    
    def __init__(self, identifier: str):
        message = f"User not found: {identifier}"
        super().__init__(message, "USER_NOT_FOUND")


class EmailAlreadyExistsException(DomainException):
    """Raised when attempting to register with an existing email"""
    
    def __init__(self, email: str):
        message = f"Email already registered: {email}"
        super().__init__(message, "EMAIL_EXISTS")


class InvalidCredentialsException(DomainException):
    """Raised when authentication credentials are invalid"""
    
    def __init__(self):
        super().__init__("Invalid email or password", "INVALID_CREDENTIALS")


class AccountNotVerifiedException(DomainException):
    """Raised when attempting to access features requiring verified account"""
    
    def __init__(self):
        super().__init__("Account email not verified", "ACCOUNT_NOT_VERIFIED")


class AccountDeactivatedException(DomainException):
    """Raised when attempting to access deactivated account"""
    
    def __init__(self):
        super().__init__("Account has been deactivated", "ACCOUNT_DEACTIVATED")


class PasswordValidationException(DomainException):
    """Raised when password doesn't meet requirements"""
    
    def __init__(self, message: str):
        super().__init__(f"Password validation failed: {message}", "PASSWORD_INVALID")


class EmailValidationException(DomainException):
    """Raised when email format is invalid"""
    
    def __init__(self, email: str):
        super().__init__(f"Invalid email format: {email}", "EMAIL_INVALID")


class UserNotFoundError(DomainException):
    """Raised when a user cannot be found"""
    
    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND")


class UserAlreadyExistsError(DomainException):
    """Raised when attempting to create a user that already exists"""
    
    def __init__(self, message: str = "User already exists"):
        super().__init__(message, "USER_ALREADY_EXISTS")


class RepositoryError(DomainException):
    """Raised when repository operations fail"""
    
    def __init__(self, message: str):
        super().__init__(f"Repository error: {message}", "REPOSITORY_ERROR")


class TokenExpiredException(DomainException):
    """Raised when a token has expired"""
    
    def __init__(self, token_type: str = "Token"):
        super().__init__(f"{token_type} has expired", "TOKEN_EXPIRED")


class UserNotVerifiedException(DomainException):
    """Raised when user email is not verified"""
    
    def __init__(self):
        super().__init__("User email address is not verified", "USER_NOT_VERIFIED")


class AccountLockedException(DomainException):
    """Raised when account is locked due to security reasons"""
    
    def __init__(self, reason: str = "Account locked"):
        super().__init__(reason, "ACCOUNT_LOCKED")