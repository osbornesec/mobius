"""
Middleware for correlation ID handling.

This middleware provides:
- Correlation ID extraction from incoming requests
- Correlation ID generation for new requests
- Correlation ID propagation to responses
- Integration with structured logging context
"""

import uuid
from typing import Optional

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import get_logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware for handling correlation IDs across requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Correlation-ID",
        generate_id_if_missing: bool = True
    ):
        super().__init__(app)
        self.header_name = header_name
        self.generate_id_if_missing = generate_id_if_missing
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle correlation ID."""
        # Extract or generate correlation ID
        correlation_id = self._get_or_generate_correlation_id(request)
        
        # Store correlation ID in request state for access by other components
        request.state.correlation_id = correlation_id
        
        # Bind correlation ID to logging context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        # Log correlation ID handling
        if self._get_correlation_id_from_headers(request):
            self.logger.debug("Using existing correlation ID", correlation_id=correlation_id)
        else:
            self.logger.debug("Generated new correlation ID", correlation_id=correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id
        
        return response
    
    def _get_correlation_id_from_headers(self, request: Request) -> Optional[str]:
        """Extract correlation ID from request headers."""
        # Check both the configured header and common variations
        headers_to_check = [
            self.header_name,
            self.header_name.lower(),
            "x-correlation-id",
            "x-request-id",
            "x-trace-id"
        ]
        
        for header in headers_to_check:
            value = request.headers.get(header)
            if value:
                return value
        
        return None
    
    def _get_or_generate_correlation_id(self, request: Request) -> str:
        """Get correlation ID from request or generate a new one."""
        correlation_id = self._get_correlation_id_from_headers(request)
        
        if not correlation_id and self.generate_id_if_missing:
            correlation_id = self._generate_correlation_id()
        
        return correlation_id or ""
    
    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID."""
        return str(uuid.uuid4())


def get_correlation_id(request: Request) -> Optional[str]:
    """
    Get the correlation ID from the current request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Correlation ID if available, None otherwise
    """
    return getattr(request.state, "correlation_id", None)