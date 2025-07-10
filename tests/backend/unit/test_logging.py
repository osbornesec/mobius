"""
Unit tests for backend logging module.

This module provides comprehensive tests for the logging system, including:
- Structured JSON logging configuration
- Request/response logging with correlation IDs
- Environment-specific log levels
- Sensitive data masking
- Performance tracking
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from pydantic import BaseModel, SecretStr

# Mock the logging module that doesn't exist yet
# This follows the expected structure from Task 002


class LogConfig(BaseModel):
    """Logging configuration settings."""
    
    level: str = "INFO"
    format: str = "json"
    correlation_id_header: str = "X-Correlation-ID"
    mask_fields: list[str] = ["password", "secret", "token", "api_key", "authorization"]
    include_process_info: bool = True
    include_timestamp: bool = True


class SensitiveDataMasker:
    """Processor for masking sensitive data in logs."""
    
    def __init__(self, mask_fields: list[str]):
        self.mask_fields = mask_fields
        self._mask_value = "***MASKED***"
    
    def __call__(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process event dict to mask sensitive fields."""
        return self._mask_dict(event_dict)
    
    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask sensitive fields in dictionaries."""
        masked = {}
        for key, value in data.items():
            if any(field in key.lower() for field in self.mask_fields):
                masked[key] = self._mask_value
            elif isinstance(value, dict):
                masked[key] = self._mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [
                    self._mask_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        return masked


def setup_logging(
    log_config: LogConfig,
    environment: str = "development"
) -> None:
    """Configure structured logging based on configuration and environment."""
    # Set log level based on environment
    if environment == "production":
        log_level = getattr(logging, log_config.level.upper(), logging.INFO)
    else:
        log_level = logging.DEBUG
    
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    # Add sensitive data masker
    processors.append(SensitiveDataMasker(log_config.mask_fields))
    
    # Environment-specific processors
    if environment == "development":
        processors.append(structlog.processors.format_exc_info)
    else:
        # In production, we want exception info but not full stack traces
        processors.append(lambda _, __, event_dict: {
            **event_dict,
            "exception": event_dict.get("exception", "").split("\n")[0] if "exception" in event_dict else None
        })
    
    # Add process info if configured
    if log_config.include_process_info:
        processors.append(structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ))
    
    # JSON renderer for structured output
    processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )


# Logging middleware for FastAPI
class LoggingMiddleware:
    """Middleware for request/response logging with correlation IDs."""
    
    def __init__(self, app: FastAPI, log_config: LogConfig):
        self.app = app
        self.log_config = log_config
        self.logger = structlog.get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        # Generate or extract correlation ID
        correlation_id = request.headers.get(
            self.log_config.correlation_id_header,
            self._generate_correlation_id()
        )
        
        # Bind correlation ID to context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=self._generate_request_id(),
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )
        
        # Log request
        start_time = time.time()
        self.logger.info(
            "request_started",
            headers=dict(request.headers),
            query_params=dict(request.query_params),
        )
        
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
    
    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid
        return str(uuid.uuid4())[:8]


# Test fixtures
@pytest.fixture
def log_config():
    """Provide default log configuration."""
    return LogConfig()


@pytest.fixture
def clean_logging():
    """Clean up logging configuration after each test."""
    yield
    # Reset structlog configuration
    structlog.reset_defaults()
    # Clear any handlers
    logger = logging.getLogger()
    logger.handlers = []


@pytest.fixture
def capture_logs():
    """Capture structured log output."""
    logs = []
    
    def capture_processor(logger, method_name, event_dict):
        logs.append(event_dict)
        return event_dict
    
    # Insert capture processor before JSON renderer
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        capture_processor,
        structlog.processors.JSONRenderer(),
    ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    return logs


# Tests
class TestStructuredLogging:
    """Test structured JSON logging configuration."""
    
    def test_json_logging_format(self, log_config, clean_logging, capture_logs):
        """Test that logs are output in JSON format."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        # Log a test message
        logger.info("test_message", key="value", number=42)
        
        # Get the last log entry
        assert len(capture_logs) > 0
        log_entry = capture_logs[-1]
        
        # Verify JSON structure
        assert "event" in log_entry
        assert log_entry["event"] == "test_message"
        assert log_entry["key"] == "value"
        assert log_entry["number"] == 42
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert log_entry["level"] == "info"
    
    def test_log_contains_required_fields(self, log_config, clean_logging, capture_logs):
        """Test that all required fields are present in log entries."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test.module")
        
        logger.warning("test_warning", custom_field="test")
        
        log_entry = capture_logs[-1]
        
        # Required fields
        assert "event" in log_entry
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry
        assert log_entry["logger"] == "test.module"
        
        # Process info (in dev mode)
        assert "filename" in log_entry
        assert "func_name" in log_entry
        assert "lineno" in log_entry
    
    def test_timestamp_format(self, log_config, clean_logging, capture_logs):
        """Test that timestamps are in ISO format."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        logger.info("test_timestamp")
        
        log_entry = capture_logs[-1]
        timestamp = log_entry["timestamp"]
        
        # Verify ISO format
        assert "T" in timestamp
        assert timestamp.endswith("Z")
        # Verify it can be parsed
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestLogLevels:
    """Test environment-specific log levels."""
    
    def test_development_log_level(self, log_config, clean_logging):
        """Test that development environment uses DEBUG level."""
        setup_logging(log_config, environment="development")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_production_log_level(self, log_config, clean_logging):
        """Test that production environment uses configured level."""
        log_config.level = "WARNING"
        setup_logging(log_config, environment="production")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
    
    def test_log_filtering_by_level(self, log_config, clean_logging, capture_logs):
        """Test that logs below configured level are filtered."""
        log_config.level = "WARNING"
        setup_logging(log_config, environment="production")
        logger = structlog.get_logger("test")
        
        # These should be filtered
        logger.debug("debug_message")
        logger.info("info_message")
        
        # These should pass
        logger.warning("warning_message")
        logger.error("error_message")
        
        # Only warning and error should be captured
        events = [log["event"] for log in capture_logs]
        assert "debug_message" not in events
        assert "info_message" not in events
        assert "warning_message" in events
        assert "error_message" in events


class TestCorrelationIDs:
    """Test correlation ID handling in logs."""
    
    @pytest.fixture
    def app(self, log_config):
        """Create FastAPI app with logging middleware."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            logger = structlog.get_logger("endpoint")
            logger.info("processing_request")
            return {"status": "ok"}
        
        # Add middleware
        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            middleware = LoggingMiddleware(app, log_config)
            return await middleware(request, call_next)
        
        return app
    
    def test_correlation_id_generation(self, app, log_config, clean_logging, capture_logs):
        """Test that correlation IDs are generated for requests."""
        setup_logging(log_config, environment="development")
        client = TestClient(app)
        
        response = client.get("/test")
        
        # Check response header
        assert log_config.correlation_id_header in response.headers
        correlation_id = response.headers[log_config.correlation_id_header]
        
        # Check logs contain correlation ID
        request_logs = [
            log for log in capture_logs 
            if log.get("event") in ["request_started", "request_completed", "processing_request"]
        ]
        
        for log in request_logs:
            assert log.get("correlation_id") == correlation_id
    
    def test_correlation_id_propagation(self, app, log_config, clean_logging, capture_logs):
        """Test that provided correlation IDs are propagated."""
        setup_logging(log_config, environment="development")
        client = TestClient(app)
        
        provided_id = "test-correlation-id-123"
        response = client.get(
            "/test",
            headers={log_config.correlation_id_header: provided_id}
        )
        
        # Check it's returned in response
        assert response.headers[log_config.correlation_id_header] == provided_id
        
        # Check it's in all relevant logs
        request_logs = [
            log for log in capture_logs 
            if log.get("event") in ["request_started", "request_completed", "processing_request"]
        ]
        
        for log in request_logs:
            assert log.get("correlation_id") == provided_id


class TestSensitiveDataMasking:
    """Test masking of sensitive data in logs."""
    
    def test_sensitive_field_masking(self, log_config, clean_logging, capture_logs):
        """Test that sensitive fields are masked."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        # Log with sensitive data
        logger.info(
            "user_login",
            username="testuser",
            password="secret123",
            api_key="sk-1234567890",
            token="bearer-token",
            safe_field="this is safe"
        )
        
        log_entry = capture_logs[-1]
        
        # Sensitive fields should be masked
        assert log_entry["password"] == "***MASKED***"
        assert log_entry["api_key"] == "***MASKED***"
        assert log_entry["token"] == "***MASKED***"
        
        # Non-sensitive fields should be intact
        assert log_entry["username"] == "testuser"
        assert log_entry["safe_field"] == "this is safe"
    
    def test_nested_sensitive_data_masking(self, log_config, clean_logging, capture_logs):
        """Test that sensitive data in nested structures is masked."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        logger.info(
            "api_call",
            request={
                "url": "https://api.example.com",
                "headers": {
                    "Authorization": "Bearer secret-token",
                    "Content-Type": "application/json"
                },
                "body": {
                    "username": "user",
                    "password": "secret",
                    "data": {
                        "api_key": "nested-secret"
                    }
                }
            }
        )
        
        log_entry = capture_logs[-1]
        request_data = log_entry["request"]
        
        # Check nested masking
        assert request_data["headers"]["Authorization"] == "***MASKED***"
        assert request_data["headers"]["Content-Type"] == "application/json"
        assert request_data["body"]["password"] == "***MASKED***"
        assert request_data["body"]["data"]["api_key"] == "***MASKED***"
        assert request_data["body"]["username"] == "user"
    
    def test_list_sensitive_data_masking(self, log_config, clean_logging, capture_logs):
        """Test that sensitive data in lists is masked."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        logger.info(
            "batch_operation",
            users=[
                {"id": 1, "username": "user1", "password": "pass1"},
                {"id": 2, "username": "user2", "token": "token2"},
            ]
        )
        
        log_entry = capture_logs[-1]
        users = log_entry["users"]
        
        assert users[0]["password"] == "***MASKED***"
        assert users[1]["token"] == "***MASKED***"
        assert users[0]["username"] == "user1"
        assert users[1]["username"] == "user2"


class TestRequestResponseLogging:
    """Test request and response logging functionality."""
    
    @pytest.fixture
    def app(self, log_config):
        """Create FastAPI app with logging middleware."""
        app = FastAPI()
        
        @app.get("/success")
        async def success_endpoint():
            return {"status": "success"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        @app.post("/data")
        async def data_endpoint(data: dict):
            return {"received": data}
        
        # Add middleware
        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            middleware = LoggingMiddleware(app, log_config)
            return await middleware(request, call_next)
        
        return app
    
    def test_request_logging(self, app, log_config, clean_logging, capture_logs):
        """Test that requests are logged with details."""
        setup_logging(log_config, environment="development")
        client = TestClient(app)
        
        response = client.get("/success?param=value", headers={"User-Agent": "TestClient"})
        
        # Find request log
        request_log = next(
            (log for log in capture_logs if log.get("event") == "request_started"),
            None
        )
        
        assert request_log is not None
        assert request_log["method"] == "GET"
        assert request_log["path"] == "/success"
        assert "headers" in request_log
        assert "query_params" in request_log
        assert request_log["query_params"]["param"] == "value"
    
    def test_response_logging(self, app, log_config, clean_logging, capture_logs):
        """Test that responses are logged with status and duration."""
        setup_logging(log_config, environment="development")
        client = TestClient(app)
        
        response = client.get("/success")
        
        # Find response log
        response_log = next(
            (log for log in capture_logs if log.get("event") == "request_completed"),
            None
        )
        
        assert response_log is not None
        assert response_log["status_code"] == 200
        assert "duration_ms" in response_log
        assert isinstance(response_log["duration_ms"], (int, float))
        assert response_log["duration_ms"] >= 0
    
    def test_error_response_logging(self, app, log_config, clean_logging, capture_logs):
        """Test that error responses are logged appropriately."""
        setup_logging(log_config, environment="development")
        client = TestClient(app)
        
        # Expect the endpoint to raise an error
        with pytest.raises(ValueError):
            response = client.get("/error")
        
        # Even with errors, we should log the request
        request_log = next(
            (log for log in capture_logs if log.get("event") == "request_started"),
            None
        )
        
        assert request_log is not None


class TestExceptionHandling:
    """Test exception handling in different environments."""
    
    def test_development_exception_with_stack_trace(self, log_config, clean_logging, capture_logs):
        """Test that full stack traces are included in development."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("error_occurred")
        
        log_entry = capture_logs[-1]
        
        assert "exception" in log_entry
        assert "Traceback" in log_entry["exception"]
        assert "ValueError: Test exception" in log_entry["exception"]
    
    def test_production_exception_without_stack_trace(self, log_config, clean_logging, capture_logs):
        """Test that stack traces are excluded in production."""
        setup_logging(log_config, environment="production")
        logger = structlog.get_logger("test")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("error_occurred")
        
        log_entry = capture_logs[-1]
        
        # In production, we should only see the exception message, not full trace
        assert "exception" in log_entry
        # Our mock implementation just takes the first line
        assert "Traceback" not in str(log_entry.get("exception", ""))


class TestPerformanceTracking:
    """Test performance and timing tracking in logs."""
    
    def test_request_duration_tracking(self, log_config, clean_logging):
        """Test that request durations are tracked accurately."""
        app = FastAPI()
        
        @app.get("/slow")
        async def slow_endpoint():
            time.sleep(0.1)  # Simulate slow operation
            return {"status": "done"}
        
        # Add middleware
        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            middleware = LoggingMiddleware(app, log_config)
            return await middleware(request, call_next)
        
        setup_logging(log_config, environment="development")
        client = TestClient(app)
        
        # Capture logs manually
        logs = []
        
        def capture_processor(logger, method_name, event_dict):
            logs.append(event_dict)
            return event_dict
        
        # Re-configure with capture
        processors = list(structlog.get_config()["processors"])
        processors.insert(-1, capture_processor)  # Insert before JSON renderer
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
        
        response = client.get("/slow")
        
        # Find response log
        response_log = next(
            (log for log in logs if log.get("event") == "request_completed"),
            None
        )
        
        assert response_log is not None
        assert response_log["duration_ms"] >= 100  # Should be at least 100ms
    
    def test_custom_timing_context(self, log_config, clean_logging, capture_logs):
        """Test custom timing contexts in logs."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        # Simulate timing a operation
        start = time.time()
        time.sleep(0.05)
        duration_ms = (time.time() - start) * 1000
        
        logger.info(
            "operation_completed",
            operation="database_query",
            duration_ms=round(duration_ms, 2)
        )
        
        log_entry = capture_logs[-1]
        
        assert log_entry["operation"] == "database_query"
        assert log_entry["duration_ms"] >= 50


class TestLoggerConfiguration:
    """Test logger configuration options."""
    
    def test_disable_process_info(self, clean_logging, capture_logs):
        """Test that process info can be disabled."""
        log_config = LogConfig(include_process_info=False)
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        logger.info("test_message")
        
        log_entry = capture_logs[-1]
        
        # Process info should not be included
        assert "filename" not in log_entry
        assert "func_name" not in log_entry
        assert "lineno" not in log_entry
    
    def test_custom_mask_fields(self, clean_logging, capture_logs):
        """Test custom sensitive field configuration."""
        log_config = LogConfig(
            mask_fields=["custom_secret", "private_key", "ssn"]
        )
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        logger.info(
            "custom_test",
            custom_secret="should be masked",
            private_key="also masked",
            ssn="123-45-6789",
            public_data="not masked"
        )
        
        log_entry = capture_logs[-1]
        
        assert log_entry["custom_secret"] == "***MASKED***"
        assert log_entry["private_key"] == "***MASKED***"
        assert log_entry["ssn"] == "***MASKED***"
        assert log_entry["public_data"] == "not masked"


class TestLoggerIntegration:
    """Test integration with other system components."""
    
    def test_multiple_loggers(self, log_config, clean_logging, capture_logs):
        """Test that multiple logger instances work correctly."""
        setup_logging(log_config, environment="development")
        
        logger1 = structlog.get_logger("module1")
        logger2 = structlog.get_logger("module2")
        
        logger1.info("message_from_module1")
        logger2.warning("message_from_module2")
        
        # Both should be captured
        events = [(log["logger"], log["event"]) for log in capture_logs]
        
        assert ("module1", "message_from_module1") in events
        assert ("module2", "message_from_module2") in events
    
    def test_context_vars_isolation(self, log_config, clean_logging, capture_logs):
        """Test that context variables are properly isolated."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        # Set context for first operation
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(operation_id="op1")
        logger.info("first_operation")
        
        # Set context for second operation
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(operation_id="op2")
        logger.info("second_operation")
        
        # Check isolation
        logs_by_event = {log["event"]: log for log in capture_logs}
        
        assert logs_by_event["first_operation"]["operation_id"] == "op1"
        assert logs_by_event["second_operation"]["operation_id"] == "op2"


class TestErrorScenarios:
    """Test error handling scenarios."""
    
    def test_logging_with_circular_reference(self, log_config, clean_logging):
        """Test that circular references don't break logging."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        # Create circular reference
        obj1 = {"name": "obj1"}
        obj2 = {"name": "obj2", "ref": obj1}
        obj1["ref"] = obj2
        
        # This should not raise an exception
        try:
            logger.info("circular_test", data=obj1)
        except Exception as e:
            pytest.fail(f"Logging with circular reference raised: {e}")
    
    def test_logging_with_non_serializable(self, log_config, clean_logging):
        """Test that non-serializable objects are handled gracefully."""
        setup_logging(log_config, environment="development")
        logger = structlog.get_logger("test")
        
        # Create non-serializable object
        class CustomObject:
            def __repr__(self):
                return "<CustomObject>"
        
        # This should not raise an exception
        try:
            logger.info("custom_object_test", obj=CustomObject())
        except Exception as e:
            pytest.fail(f"Logging with custom object raised: {e}")