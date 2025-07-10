"""
Core logging configuration using structlog.

This module provides structured JSON logging configuration with:
- Environment-specific log levels
- Sensitive data masking
- Process information tracking
- Structured JSON output for production
- Pretty console output for development
"""

import logging
import os
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field


class LogConfig(BaseModel):
    """Logging configuration settings."""
    
    level: str = Field("INFO", description="Default log level")
    format: str = Field("json", description="Log format (json or console)")
    correlation_id_header: str = Field("X-Correlation-ID", description="Header name for correlation ID")
    mask_fields: List[str] = Field(
        default_factory=lambda: ["password", "secret", "token", "api_key", "authorization"],
        description="Field names to mask in logs"
    )
    include_process_info: bool = Field(True, description="Include process information in logs")
    include_timestamp: bool = Field(True, description="Include timestamps in logs")


class SensitiveDataMasker:
    """Processor for masking sensitive data in logs."""
    
    def __init__(self, mask_fields: List[str]):
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
    log_config: Optional[LogConfig] = None,
    environment: Optional[str] = None
) -> None:
    """
    Configure structured logging based on configuration and environment.
    
    Args:
        log_config: Logging configuration settings
        environment: Environment name (development, production, etc.)
    """
    if log_config is None:
        log_config = LogConfig()
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
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
        def format_exception_short(_, __, event_dict):
            if "exception" in event_dict and event_dict["exception"]:
                # Extract just the exception type and message
                exc_lines = str(event_dict["exception"]).split("\n")
                if exc_lines:
                    # Keep only the first line (exception type and message)
                    event_dict["exception"] = exc_lines[0]
            return event_dict
        
        processors.append(format_exception_short)
    
    # Add process info if configured
    if log_config.include_process_info:
        processors.append(structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ))
    
    # Choose renderer based on environment
    if environment == "development" and log_config.format != "json":
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON renderer for production or when explicitly requested
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


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)