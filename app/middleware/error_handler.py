"""
Global error handling middleware for Mobius Context Platform.

This module implements comprehensive error handling middleware that catches
all exceptions, formats them consistently, and ensures proper logging and
response formatting for the API.
"""

import time
import traceback
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    MobiusException,
    ErrorCode,
)
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class ErrorResponse:
    """
    Standardized error response format.

    Ensures all error responses follow a consistent structure
    with proper error codes, messages, and debugging information.
    """

    @staticmethod
    def create(
        error_code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generates a standardized error response dictionary for API error handling.

        Args:
            error_code (str): A standardized error code representing the error type.
            message (str): A human-readable description of the error.
            details (Optional[dict[str, Any]]): Additional context or metadata about the error.
            request_id (Optional[str]): The correlation ID for the request, if available.
            path (Optional[str]): The request path where the error occurred.

        Returns:
            dict[str, Any]: A dictionary containing the error code, message, optional details, request ID, path, and a timestamp, formatted for consistent API error responses.

        Example:
            response = ErrorResponse.create(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
                details={"trace": "stacktrace info"},
                request_id="abc-123",
                path="/api/resource"
            )

        Raises:
            This function does not raise exceptions.

        Generated by CodeRabbit
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
            },
            "success": False,
        }

        if details:
            response["error"]["details"] = details

        if request_id:
            response["request_id"] = request_id

        if path:
            response["path"] = path

        # Add timestamp
        response["timestamp"] = int(time.time())

        return response


def get_correlation_id(request: Request) -> Optional[str]:
    """
    Extracts the correlation ID from the FastAPI request object.

    Attempts to retrieve the correlation ID from the request's state (if set by CorrelationIdMiddleware)
    or from various correlation headers. Returns the correlation ID as a string if found, otherwise returns None.

    Checks for correlation_id in request state (set by CorrelationIdMiddleware)
    or falls back to checking common correlation headers.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        Optional[str]: The correlation ID as a string if available, otherwise None.

    Generated by CodeRabbit
    """
    # Try to get from state (set by correlation middleware)
    if hasattr(request.state, "correlation_id"):
        correlation_id = request.state.correlation_id
        if isinstance(correlation_id, UUID):
            return str(correlation_id)
        return correlation_id

    # Try to get from headers - check common variations
    headers_to_check = [
        "X-Correlation-ID",
        "X-Request-ID",
        "X-Trace-ID",
        "x-correlation-id",
        "x-request-id",
        "x-trace-id",
    ]

    for header in headers_to_check:
        value = request.headers.get(header)
        if value:
            return value

    return None


async def handle_mobius_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handles Mobius platform-specific exceptions and returns a standardized JSON error response.

    Args:
        request (Request): The incoming FastAPI request object.
        exc (MobiusException): The MobiusException instance containing error details.

    Returns:
        JSONResponse: A JSON response with the error code, message, details, request ID, and request path, using the exception's status code.

    Raises:
        None

    Example:
        async def some_route(request: Request):
            raise MobiusException(
                error_code=ErrorCode.INVALID_INPUT,
                message="Invalid input provided.",
                status_code=400,
                details={"field": "username"}
            )
        # This will be handled by handle_mobius_exception and return a structured error response.

    Generated by CodeRabbit
    """
    # Cast to specific exception type
    if not isinstance(exc, MobiusException):
        return await handle_generic_exception(request, exc)
    mobius_exc: MobiusException = exc

    correlation_id = get_correlation_id(request)

    # Log the error with appropriate level
    if mobius_exc.status_code >= 500:
        logger.error(
            f"Internal error: {mobius_exc.message}",
            extra={
                "error_code": mobius_exc.error_code.value,
                "status_code": mobius_exc.status_code,
                "details": mobius_exc.details,
                "correlation_id": correlation_id,
                "path": request.url.path,
            },
            exc_info=True,
        )
    else:
        logger.warning(
            f"Client error: {mobius_exc.message}",
            extra={
                "error_code": mobius_exc.error_code.value,
                "status_code": mobius_exc.status_code,
                "details": mobius_exc.details,
                "correlation_id": correlation_id,
                "path": request.url.path,
            },
        )

    # Create response
    response_data = ErrorResponse.create(
        error_code=mobius_exc.error_code.value,
        message=mobius_exc.message,
        details=mobius_exc.details,
        request_id=correlation_id,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=mobius_exc.status_code,
        content=response_data,
    )


async def handle_validation_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handles FastAPI request validation errors and returns a standardized JSON response with detailed validation error information.

    Args:
        request (Request): The incoming FastAPI request object.
        exc (RequestValidationError): The exception containing validation error details.

    Returns:
        JSONResponse: A response with HTTP status 422 and a structured payload describing the validation errors.

    Example:
        When a request fails validation, this handler extracts error details, logs them, and returns a JSON response:
            {
                "error_code": "validation_error",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": [
                        {
                            "field": "body.username",
                            "message": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                },
                "request_id": "abc123",
                "path": "/api/resource",
                "timestamp": "2024-06-01T12:00:00Z"
            }

    Generated by CodeRabbit
    """
    # Cast to specific exception type
    if not isinstance(exc, RequestValidationError):
        return await handle_generic_exception(request, exc)
    validation_exc: RequestValidationError = exc

    correlation_id = get_correlation_id(request)

    # Format validation errors
    errors = []
    for error in validation_exc.errors():
        error_dict = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        if "ctx" in error:
            error_dict["context"] = error["ctx"]
        errors.append(error_dict)

    logger.warning(
        "Validation error",
        extra={
            "errors": errors,
            "correlation_id": correlation_id,
            "path": request.url.path,
        },
    )

    # Create response
    response_data = ErrorResponse.create(
        error_code=ErrorCode.VALIDATION_ERROR.value,
        message="Request validation failed",
        details={"validation_errors": errors},
        request_id=correlation_id,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def handle_pydantic_validation_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handles Pydantic validation errors and returns a standardized JSON response.

    Args:
        request (Request): The incoming FastAPI request object.
        exc (PydanticValidationError): The Pydantic validation error.

    Returns:
        JSONResponse: A response with HTTP status 422 and validation error details.
    """
    # Cast to specific exception type
    if not isinstance(exc, PydanticValidationError):
        return await handle_generic_exception(request, exc)
    pydantic_exc: PydanticValidationError = exc

    correlation_id = get_correlation_id(request)

    # Format Pydantic validation errors
    errors = []
    for error in pydantic_exc.errors():
        error_dict: Dict[str, Any] = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        if "ctx" in error:
            error_dict["context"] = error["ctx"]
        errors.append(error_dict)

    logger.warning(
        "Pydantic validation error",
        extra={
            "errors": errors,
            "correlation_id": correlation_id,
            "path": request.url.path,
        },
    )

    # Create response
    response_data = ErrorResponse.create(
        error_code=ErrorCode.VALIDATION_ERROR.value,
        message="Data validation failed",
        details={"validation_errors": errors},
        request_id=correlation_id,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def handle_http_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handles HTTP exceptions raised by FastAPI or Starlette, mapping them to standardized error codes and returning a consistent JSON error response.

    Args:
        request (Request): The incoming FastAPI request object.
        exc (HTTPException): The HTTP exception instance to handle.

    Returns:
        JSONResponse: A JSON response containing the standardized error code, message, request ID, and path, with the original HTTP status code and headers.

    Example:
        When a route raises an HTTPException (e.g., 404 Not Found), this handler returns a JSON response with an appropriate error code and message.

    Generated by CodeRabbit
    """
    # Cast to specific exception type
    if not isinstance(exc, (HTTPException, StarletteHTTPException)):
        return await handle_generic_exception(request, exc)
    http_exc = exc

    correlation_id = get_correlation_id(request)

    # Map status codes to error codes
    error_code_mapping = {
        status.HTTP_400_BAD_REQUEST: ErrorCode.VALIDATION_ERROR,
        status.HTTP_401_UNAUTHORIZED: ErrorCode.UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN: ErrorCode.FORBIDDEN,
        status.HTTP_404_NOT_FOUND: ErrorCode.NOT_FOUND,
        status.HTTP_405_METHOD_NOT_ALLOWED: ErrorCode.METHOD_NOT_ALLOWED,
        status.HTTP_409_CONFLICT: ErrorCode.CONFLICT,
        status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.RATE_LIMIT_EXCEEDED,
    }

    error_code = error_code_mapping.get(
        http_exc.status_code,
        ErrorCode.INTERNAL_ERROR,
    )

    logger.warning(
        f"HTTP exception: {http_exc.detail}",
        extra={
            "status_code": http_exc.status_code,
            "correlation_id": correlation_id,
            "path": request.url.path,
        },
    )

    # Create response
    response_data = ErrorResponse.create(
        error_code=error_code.value,
        message=http_exc.detail,
        request_id=correlation_id,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=http_exc.status_code,
        content=response_data,
        headers=http_exc.headers,
    )


async def handle_generic_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handles unexpected exceptions not caught by other handlers, logs the error with contextual information, and returns a standardized JSON error response.

    Args:
        request (Request): The incoming FastAPI request object.
        exc (Exception): The uncaught exception instance.

    Returns:
        JSONResponse: A JSON response containing a standardized error structure with error code, message, optional details, request ID, and request path. In production, internal details are omitted; in non-production, exception type and traceback are included.

    Raises:
        None

    Example:
        This function is registered as a global exception handler in FastAPI to ensure all unhandled exceptions are logged and returned in a consistent format.

    Generated by CodeRabbit
    """
    correlation_id = get_correlation_id(request)

    # Log the full exception
    logger.exception(
        f"Unexpected error: {exc!s}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "exception_type": type(exc).__name__,
        },
    )

    # Create response - don't expose internal details in production
    if settings.is_production():
        message = "An internal error occurred"
        details = None
    else:
        message = str(exc)
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n"),
        }

    response_data = ErrorResponse.create(
        error_code=ErrorCode.INTERNAL_ERROR.value,
        message=message,
        details=details,
        request_id=correlation_id,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers for the FastAPI application to ensure consistent error handling and response formatting.

    Args:
        app (FastAPI): The FastAPI application instance to which exception handlers will be attached.

    Returns:
        None: This function does not return a value.

    Raises:
        None

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> setup_exception_handlers(app)

    Generated by CodeRabbit
    """
    # Handle our custom exceptions
    app.add_exception_handler(MobiusException, handle_mobius_exception)

    # Handle validation errors
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(PydanticValidationError, handle_pydantic_validation_error)

    # Handle HTTP exceptions
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)

    # Handle all other exceptions
    app.add_exception_handler(Exception, handle_generic_exception)

    logger.info("Exception handlers registered")


class ErrorHandlerMiddleware:
    """
    Middleware for catching errors that slip through exception handlers.

    This acts as a safety net for any errors not caught by the
    exception handlers, ensuring no errors go unhandled.
    """

    def __init__(self, app: FastAPI) -> None:
        """
        Initializes the ErrorHandlerMiddleware with the provided FastAPI application instance.

        Args:
            app (FastAPI): The FastAPI application to which this middleware will be attached.

        Generated by CodeRabbit
        """
        self.app = app

    async def __call__(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Handles incoming requests and catches any uncaught exceptions, ensuring a consistent JSON error response.

        Args:
            request (Request): The incoming FastAPI request object.
            call_next (Callable): The next middleware or endpoint to process the request.

        Returns:
            Response: The HTTP response, either from downstream processing or a generic internal error response if an uncaught exception occurs.

        Raises:
            Exception: Propagates only if an unexpected error occurs outside the try block.

        Example:
            # Used as part of FastAPI middleware stack
            app.add_middleware(ErrorHandlerMiddleware)

        Generated by CodeRabbit
        """
        try:
            return await call_next(request)

        except Exception:
            # This should rarely be hit as exception handlers should catch most errors
            logger.exception(
                "Uncaught exception in middleware",
                extra={
                    "correlation_id": get_correlation_id(request),
                    "path": request.url.path,
                    "method": request.method,
                },
            )

            # Return a generic error response
            response_data = ErrorResponse.create(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                message="An internal error occurred",
                request_id=get_correlation_id(request),
                path=request.url.path,
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data,
            )
