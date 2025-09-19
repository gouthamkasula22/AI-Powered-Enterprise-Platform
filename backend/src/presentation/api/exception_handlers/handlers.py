"""
Exception Handlers

FastAPI exception handlers for domain exceptions and HTTP errors.
Maps domain exceptions to appropriate HTTP status codes and responses.
"""

import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from typing import Dict, Any
from datetime import datetime

from ....domain.exceptions.domain_exceptions import (
    DomainException, ValidationError as DomainValidationError,
    UserNotFoundException, EmailAlreadyExistsException,
    InvalidCredentialsException, TokenExpiredException,
    UserNotVerifiedException, AccountLockedException
)

logger = logging.getLogger(__name__)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    Handle domain exceptions and map to appropriate HTTP status codes
    """
    
    # Log the exception
    logger.warning(f"Domain exception: {type(exc).__name__}: {str(exc)}")
    
    # Map domain exceptions to HTTP status codes
    status_code_mapping = {
        UserNotFoundException: status.HTTP_404_NOT_FOUND,
        EmailAlreadyExistsException: status.HTTP_409_CONFLICT,
        InvalidCredentialsException: status.HTTP_401_UNAUTHORIZED,
        TokenExpiredException: status.HTTP_401_UNAUTHORIZED,
        UserNotVerifiedException: status.HTTP_403_FORBIDDEN,
        AccountLockedException: status.HTTP_423_LOCKED,
        DomainValidationError: status.HTTP_400_BAD_REQUEST,
    }
    
    # Error code mapping
    error_code_mapping = {
        UserNotFoundException: "USER_NOT_FOUND",
        EmailAlreadyExistsException: "EMAIL_ALREADY_EXISTS",
        InvalidCredentialsException: "INVALID_CREDENTIALS",
        TokenExpiredException: "TOKEN_EXPIRED",
        UserNotVerifiedException: "EMAIL_NOT_VERIFIED",
        AccountLockedException: "ACCOUNT_LOCKED",
        DomainValidationError: "VALIDATION_ERROR",
    }
    
    # Get appropriate status code and error code
    status_code = status_code_mapping.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    error_code = error_code_mapping.get(type(exc), "DOMAIN_ERROR")
    
    # Create error response
    error_response: Dict[str, Any] = {
        "error": error_code,
        "message": str(exc),
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }
    
    # Add additional context for specific exceptions
    if isinstance(exc, DomainValidationError):
        details = getattr(exc, 'details', None)
        if details is not None:
            error_response["details"] = str(details)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors from request parsing
    """
    
    logger.warning(f"Request validation error: {exc.errors()}")
    
    # Format validation errors
    field_errors = {}
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        field_errors[field_path] = error["msg"]
    
    error_response = {
        "error": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "field_errors": field_errors,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions
    """
    
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    # If detail is already a dict (from our endpoints), use it directly
    if isinstance(exc.detail, dict):
        error_response = exc.detail.copy()
        error_response.update({
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        })
    else:
        # Create standardized error response
        error_response = {
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=getattr(exc, 'headers', None)
    )


async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions (fallback for framework errors)
    """
    
    logger.warning(f"Starlette HTTP exception: {exc.status_code} - {exc.detail}")
    
    error_response = {
        "error": f"HTTP_{exc.status_code}",
        "message": exc.detail,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions (catch-all)
    """
    
    # Log the full exception with traceback
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    # Don't expose internal errors in production
    error_response: Dict[str, Any] = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred. Please try again later.",
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }
    
    # In development, include more details
    import os
    if os.getenv("ENVIRONMENT", "production").lower() in ["development", "dev", "local"]:
        error_response["debug"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app
    """
    
    # Domain exceptions
    app.add_exception_handler(DomainException, domain_exception_handler)
    
    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
    
    # General exception handler (catch-all)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")