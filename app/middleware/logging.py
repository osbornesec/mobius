"""
FastAPI middleware for request/response logging.

This middleware provides:
- Request and response logging with timing
- Correlation ID generation and propagation
- Structured logging with context
- Error handling and logging
"""

import time
import uuid
from typing import Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import LogConfig, get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs."""
    
    def __init__(self, app: ASGIApp, log_config: Optional[LogConfig] = None):
        super().__init__(app)
        self.log_config = log_config or LogConfig()
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log request/response information."""
        # Generate or extract correlation ID
        correlation_id = request.headers.get(
            self.log_config.correlation_id_header,
            self._generate_correlation_id()
        )
        
        # Generate request ID
        request_id = self._generate_request_id()
        
        # Bind correlation ID and request context to logger
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            client_host=request.client.host if request.client else None,
        )
        
        # Log request
        start_time = time.time()
        self.logger.info(
            "request_started",
            headers=dict(request.headers),
            query_params=dict(request.query_params),
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            self.logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
            # Add correlation ID to response headers
            response.headers[self.log_config.correlation_id_header] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.error(
                "request_failed",
                status_code=500,
                duration_ms=round(duration_ms, 2),
                error=str(e),
                exc_info=True,
            )
            
            # Re-raise the exception to let FastAPI handle it
            raise
    
    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID."""
        return str(uuid.uuid4())
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())[:8]