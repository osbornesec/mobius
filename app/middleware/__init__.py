"""
Middleware package for the Mobius platform.

This package provides FastAPI middleware for:
- Request/response logging
- Correlation ID handling
- Performance tracking
- Error handling
- Security headers (future)
- Rate limiting (future)
"""

from app.middleware.correlation import CorrelationIdMiddleware, get_correlation_id
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handler import (
    ErrorHandlerMiddleware,
    setup_exception_handlers,
    ErrorResponse,
)

__all__ = [
    "CorrelationIdMiddleware",
    "LoggingMiddleware",
    "ErrorHandlerMiddleware",
    "setup_exception_handlers",
    "ErrorResponse",
    "get_correlation_id",
]