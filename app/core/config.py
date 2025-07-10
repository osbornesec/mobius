"""
Backend configuration module for Mobius Context Platform.

This module provides type-safe configuration management using Pydantic Settings,
supporting environment variables, .env files, and environment-specific configurations.
All environment variables are prefixed with MOBIUS_ for namespace isolation.
"""

from typing import List
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    """
    Database configuration settings.
    
    Handles PostgreSQL and SQLite connection parameters with connection pooling
    settings for optimal performance.
    """
    
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, description="Maximum overflow connections")
    
    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate database URL format.
        
        Args:
            v: Database URL string
            
        Returns:
            str: Validated database URL
            
        Raises:
            ValueError: If URL format is invalid
        """
        if not v.startswith(("postgresql://", "postgres://", "sqlite:///")):
            raise ValueError("Invalid database URL format")
        return v


class RedisConfig(BaseModel):
    """
    Redis configuration settings.
    
    Manages Redis connection and caching parameters.
    """
    
    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    ttl: int = Field(
        default=3600,
        ge=1,
        description="Default TTL for cache entries in seconds"
    )


class SecurityConfig(BaseModel):
    """
    Security-related configuration.
    
    Manages JWT tokens, CORS settings, and application secrets.
    """
    
    secret_key: SecretStr = Field(..., description="Application secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_minutes: int = Field(
        default=30,
        ge=1,
        description="JWT token expiration time in minutes"
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed CORS origins"
    )


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    This class manages all configuration for the Mobius platform,
    loading from environment variables with proper validation.
    
    Environment variables should be prefixed with MOBIUS_ and use
    double underscore (__) for nested configuration.
    
    Example:
        MOBIUS_DATABASE__URL=postgresql://user:pass@localhost/db
        MOBIUS_SECURITY__SECRET_KEY=your-secret-key
    """
    
    model_config = SettingsConfigDict(
        env_prefix="MOBIUS_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        extra="ignore",
        frozen=True  # Make settings immutable
    )
    
    # Application settings
    app_name: str = Field(
        default="Mobius Context Platform",
        description="Application name"
    )
    environment: str = Field(
        default="development",
        description="Deployment environment"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )
    
    # Component configurations
    database: DatabaseConfig = Field(
        ...,
        description="Database configuration"
    )
    redis: RedisConfig = Field(
        default_factory=RedisConfig,
        description="Redis configuration"
    )
    security: SecurityConfig = Field(
        ...,
        description="Security configuration"
    )
    
    # Feature flags
    enable_analytics: bool = Field(
        default=True,
        description="Enable analytics collection"
    )
    enable_cache: bool = Field(
        default=True,
        description="Enable caching layer"
    )
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate environment is one of the allowed values.
        
        Args:
            v: Environment name
            
        Returns:
            str: Validated environment name
            
        Raises:
            ValueError: If environment is not allowed
        """
        allowed = ["development", "staging", "production", "test"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """
        Validate port is in valid range.
        
        Args:
            v: Port number
            
        Returns:
            int: Validated port number
            
        Raises:
            ValueError: If port is out of valid range
        """
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    def __repr__(self) -> str:
        """
        Safe representation that doesn't expose sensitive values.
        
        Returns:
            str: String representation without sensitive data
        """
        return f"<Settings environment={self.environment}>"
    
    def is_production(self) -> bool:
        """
        Check if running in production environment.
        
        Returns:
            bool: True if in production
        """
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """
        Check if running in development environment.
        
        Returns:
            bool: True if in development
        """
        return self.environment == "development"
    
    def is_test(self) -> bool:
        """
        Check if running in test environment.
        
        Returns:
            bool: True if in test
        """
        return self.environment == "test"


# Singleton pattern for settings
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).
    
    This function ensures only one Settings instance is created,
    improving performance by avoiding repeated environment variable parsing.
    
    Returns:
        Settings: Cached settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """
    Reset the cached settings instance.
    
    This is primarily useful for testing when you need to reload
    settings with different environment variables.
    """
    global _settings
    _settings = None