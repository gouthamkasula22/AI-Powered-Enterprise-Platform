"""
Domain Exceptions - Business rule violations
"""

from .domain_exceptions import (
    DomainException,
    ValidationError,
    UserNotFoundException,
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    AccountNotVerifiedException,
    AccountDeactivatedException,
    PasswordValidationException,
    EmailValidationException,
    UserNotFoundError,
    UserAlreadyExistsError,
    RepositoryError
)

__all__ = [
    "DomainException",
    "ValidationError", 
    "UserNotFoundException",
    "EmailAlreadyExistsException",
    "InvalidCredentialsException",
    "AccountNotVerifiedException",
    "AccountDeactivatedException",
    "PasswordValidationException",
    "EmailValidationException",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "RepositoryError"
]