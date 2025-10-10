"""Custom exceptions for Project Agent."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ProjectAgentException(Exception):
    """Base exception for Project Agent."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DocumentNotFoundError(ProjectAgentException):
    """Document not found exception."""
    pass


class AuthenticationError(ProjectAgentException):
    """Authentication failure exception."""
    pass


class AuthorizationError(ProjectAgentException):
    """Authorization failure exception."""
    pass


class ValidationError(ProjectAgentException):
    """Validation error exception."""
    pass


class ProcessingError(ProjectAgentException):
    """Document processing error exception."""
    pass


class StorageError(ProjectAgentException):
    """Storage operation error exception."""
    pass


class ExternalServiceError(ProjectAgentException):
    """External service error exception."""
    pass


def handle_exception(exc: Exception) -> HTTPException:
    """
    Convert custom exceptions to HTTP exceptions.
    
    Args:
        exc: Exception to convert
        
    Returns:
        HTTPException with appropriate status code
    """
    if isinstance(exc, DocumentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "document_not_found",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, AuthenticationError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_failed",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "authorization_failed",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    elif isinstance(exc, (ProcessingError, StorageError, ExternalServiceError)):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": exc.message,
                "details": exc.details
            }
        )
    
    else:
        # Unknown exception
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "unknown_error",
                "message": "An unexpected error occurred",
                "details": {"exception_type": type(exc).__name__}
            }
        )

