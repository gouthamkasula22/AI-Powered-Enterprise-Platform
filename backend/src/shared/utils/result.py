"""
Result pattern implementation for error handling.

Provides a standardized way to return success/failure results
with associated data or error messages.
"""

from typing import TypeVar, Generic, Optional, Any, Dict


T = TypeVar('T')


class Result(Generic[T]):
    """
    Result pattern implementation for returning success/failure
    with associated data or error messages.
    """
    
    def __init__(
        self,
        is_success: bool,
        value: Optional[T] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.is_success = is_success
        self.value = value
        self.error = error
        self.error_code = error_code
        self.metadata = metadata or {}
    
    @classmethod
    def success(cls, value: T, metadata: Optional[Dict[str, Any]] = None) -> 'Result[T]':
        """Create a successful result with value"""
        return cls(True, value=value, metadata=metadata)
    
    @classmethod
    def failure(
        cls, 
        error: str, 
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Result[T]':
        """Create a failure result with error message"""
        return cls(False, error=error, error_code=error_code, metadata=metadata)
    
    def __bool__(self) -> bool:
        """Allow using the result in boolean context"""
        return self.is_success
    
    def __repr__(self) -> str:
        if self.is_success:
            return f"Success[{self.value}]"
        return f"Failure[{self.error_code or 'ERROR'}: {self.error}]"