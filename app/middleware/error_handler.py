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
    ValidationError,
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
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            error_code: Standardized error code
            message: Human-readable error message
            details: Additional error context
            request_id: Request correlation ID
            path: Request path
            
        Returns:
            Dict containing formatted error response
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


def get_request_id(request: Request) -> Optional[str]:
    """
    Extract request ID from request headers or state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID if available
    """
    # Try to get from state (set by correlation middleware)
    if hasattr(request.state, "request_id"):
        request_id = request.state.request_id
        if isinstance(request_id, UUID):
            return str(request_id)
        return request_id
    
    # Try to get from headers
    return request.headers.get("X-Request-ID")


async def handle_mobius_exception(
    request: Request,
    exc: MobiusException,
) -> JSONResponse:
    """
    Handle Mobius platform exceptions.
    
    Args:
        request: FastAPI request object
        exc: MobiusException instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = get_request_id(request)
    
    # Log the error with appropriate level
    if exc.status_code >= 500:
        logger.error(
            f"Internal error: {exc.message}",
            extra={
                "error_code": exc.error_code.value,
                "status_code": exc.status_code,
                "details": exc.details,
                "request_id": request_id,
                "path": request.url.path,
            },
            exc_info=True,
        )
    else:
        logger.warning(
            f"Client error: {exc.message}",
            extra={
                "error_code": exc.error_code.value,
                "status_code": exc.status_code,
                "details": exc.details,
                "request_id": request_id,
                "path": request.url.path,
            },
        )
    
    # Create response
    response_data = ErrorResponse.create(
        error_code=exc.error_code.value,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI request validation errors.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with validation error details
    """
    request_id = get_request_id(request)
    
    # Format validation errors
    errors = []
    for error in exc.errors():
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
            "request_id": request_id,
            "path": request.url.path,
        },
    )
    
    # Create response
    response_data = ErrorResponse.create(
        error_code=ErrorCode.VALIDATION_ERROR.value,
        message="Request validation failed",
        details={"validation_errors": errors},
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def handle_http_exception(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Handle FastAPI/Starlette HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTPException instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = get_request_id(request)
    
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
        exc.status_code,
        ErrorCode.INTERNAL_ERROR,
    )
    
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path,
        },
    )
    
    # Create response
    response_data = ErrorResponse.create(
        error_code=error_code.value,
        message=exc.detail,
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers,
    )


async def handle_generic_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = get_request_id(request)
    
    # Log the full exception
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
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
        request_id=request_id,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI app.
    
    This function sets up handlers for all types of exceptions
    that the application might encounter.
    
    Args:
        app: FastAPI application instance
    """
    # Handle our custom exceptions
    app.add_exception_handler(MobiusException, handle_mobius_exception)
    
    # Handle validation errors
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(PydanticValidationError, handle_validation_error)
    
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
        Initialize the middleware.
        
        Args:
            app: FastAPI application instance
        """
        self.app = app
        
    async def __call__(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process the request and handle any uncaught exceptions.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint
            
        Returns:
            Response object
        """
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # This should rarely be hit as exception handlers should catch most errors
            logger.error(
                f"Uncaught exception in middleware: {str(exc)}",
                extra={
                    "request_id": get_request_id(request),
                    "path": request.url.path,
                    "method": request.method,
                },
                exc_info=True,
            )
            
            # Return a generic error response
            response_data = ErrorResponse.create(
                error_code=ErrorCode.INTERNAL_ERROR.value,
                message="An internal error occurred",
                request_id=get_request_id(request),
                path=request.url.path,
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_data,
            )