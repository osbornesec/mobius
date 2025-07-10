"""
Core module for the Mobius platform.

This module provides fundamental components including:
- Configuration management
- Custom exceptions
- Logging setup
- Common utilities
"""

from app.core.config import Settings, get_settings, reset_settings
from app.core.logging import get_logger, setup_logging
from app.core.exceptions import (
    # Base exceptions
    MobiusException,
    ErrorCode,
    
    # General exceptions
    ValidationError,
    NotFoundError,
    ConflictError,
    
    # Authentication exceptions
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    
    # Authorization exceptions
    AuthorizationError,
    InsufficientPermissionsError,
    
    # Rate limiting exceptions
    RateLimitError,
    RateLimitExceededError,
    QuotaExceededError,
    
    # Business logic exceptions
    BusinessLogicError,
    ResourceLockedError,
    
    # External service exceptions
    ExternalServiceError,
    VectorDatabaseError,
    StorageError,
    
    # Context-specific exceptions
    ContextError,
    ContextNotFoundError,
    ContextTooLargeError,
    EmbeddingError,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "reset_settings",
    
    # Logging
    "get_logger",
    "setup_logging",
    
    # Error codes
    "ErrorCode",
    
    # Base exceptions
    "MobiusException",
    
    # General exceptions
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    
    # Authentication exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    
    # Authorization exceptions
    "AuthorizationError",
    "InsufficientPermissionsError",
    
    # Rate limiting exceptions
    "RateLimitError",
    "RateLimitExceededError",
    "QuotaExceededError",
    
    # Business logic exceptions
    "BusinessLogicError",
    "ResourceLockedError",
    
    # External service exceptions
    "ExternalServiceError",
    "VectorDatabaseError",
    "StorageError",
    
    # Context-specific exceptions
    "ContextError",
    "ContextNotFoundError",
    "ContextTooLargeError",
    "EmbeddingError",
]