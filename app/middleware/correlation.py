"""
Middleware for correlation ID handling.

This middleware provides:
- Correlation ID extraction from incoming requests
- Correlation ID generation for new requests
- Correlation ID propagation to responses
- Integration with structured logging context
"""

import uuid
from typing import Callable, Optional

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.logging import get_logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware for handling correlation IDs across requests."""

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Correlation-ID",
        generate_id_if_missing: bool = True,
    ) -> None:
        """
        Initializes the CorrelationIdMiddleware for managing correlation IDs in HTTP requests and responses.

        Args:
            app (ASGIApp): The ASGI application instance to wrap with the middleware.
            header_name (str, optional): The HTTP header name to use for the correlation ID. Defaults to "X-Correlation-ID".
            generate_id_if_missing (bool, optional): Whether to generate a new correlation ID if one is not found in the request headers. Defaults to True.

        Generated by CodeRabbit
        """
        super().__init__(app)
        self.header_name = header_name
        self.generate_id_if_missing = generate_id_if_missing
        self.logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processes an incoming HTTP request to extract or generate a correlation ID, binds it to the request context and logging, and ensures it is included in the response headers.

        Args:
            request (Request): The incoming FastAPI or Starlette request object.
            call_next (Callable): The next middleware or route handler to process the request.

        Returns:
            Response: The HTTP response with the correlation ID added to the response headers.

        Example:
            # Usage within FastAPI middleware stack
            app.add_middleware(CorrelationIdMiddleware, header_name="X-Correlation-ID")

        Generated by CodeRabbit
        """
        # Try to get correlation ID from headers first
        existing_correlation_id = self._get_correlation_id_from_headers(request)

        if existing_correlation_id:
            # Use existing correlation ID from headers
            correlation_id = existing_correlation_id
            correlation_id_source = "existing"
            self.logger.debug(
                "Using existing correlation ID from headers",
                correlation_id=correlation_id,
                source=correlation_id_source,
            )
        else:
            # Generate new correlation ID if none exists and generation is enabled
            if self.generate_id_if_missing:
                correlation_id = self._generate_correlation_id()
                correlation_id_source = "generated"
                self.logger.debug(
                    "Generated new correlation ID",
                    correlation_id=correlation_id,
                    source=correlation_id_source,
                )
            else:
                correlation_id = ""
                correlation_id_source = "none"
                self.logger.debug("No correlation ID found and generation disabled")

        # Store correlation ID in request state for access by other components
        request.state.correlation_id = correlation_id
        request.state.correlation_id_source = correlation_id_source

        # Bind correlation ID to logging context
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id, correlation_id_source=correlation_id_source
        )

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id

        return response

    def _get_correlation_id_from_headers(self, request: Request) -> Optional[str]:
        """
        Extracts the correlation ID from the incoming HTTP request headers.

        Checks for the correlation ID in several possible header names, including the configured header name, its lowercase variant, and common alternatives such as "x-correlation-id", "x-request-id", and "x-trace-id". Returns the first found correlation ID value, or None if none are present.

        Args:
            request (Request): The incoming FastAPI or Starlette request object.

        Returns:
            Optional[str]: The correlation ID if found in the headers, otherwise None.

        Generated by CodeRabbit
        """
        # Check both the configured header and common variations
        headers_to_check = [
            self.header_name,
            self.header_name.lower(),
            "x-correlation-id",
            "x-request-id",
            "x-trace-id",
        ]

        for header in headers_to_check:
            value = request.headers.get(header)
            if value:
                return value

        return None

    def _generate_correlation_id(self) -> str:
        """
        Generates a new unique correlation ID using UUID version 4.

        Returns:
            str: A newly generated UUID4 string to be used as a correlation ID.

        Generated by CodeRabbit
        """
        return str(uuid.uuid4())


def get_correlation_id(request: Request) -> Optional[str]:
    """
    Retrieves the correlation ID associated with the given FastAPI request.

    Args:
        request (Request): The FastAPI request object from which to extract the correlation ID.

    Returns:
        Optional[str]: The correlation ID string if present in the request state; otherwise, None.

    Generated by CodeRabbit
    """
    return getattr(request.state, "correlation_id", None)
