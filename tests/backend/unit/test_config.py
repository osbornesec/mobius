"""
Unit tests for backend configuration module.

This module provides comprehensive tests for the configuration management system,
including environment variable loading, validation, environment-specific settings,
and sensitive data handling.
"""

import os
from typing import Any, Dict
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Import the actual implementation
from app.core.config import DatabaseConfig, RedisConfig, SecurityConfig, Settings


# Test fixtures
@pytest.fixture
def clean_env(monkeypatch):
    """Remove all MOBIUS_ prefixed environment variables."""
    for key in list(os.environ.keys()):
        if key.startswith("MOBIUS_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def basic_env(monkeypatch):
    """Set up basic required environment variables."""
    monkeypatch.setenv("MOBIUS_DATABASE__URL", "postgresql://user:pass@localhost/mobius")
    monkeypatch.setenv("MOBIUS_SECURITY__SECRET_KEY", "test-secret-key-123")


@pytest.fixture
def full_env(monkeypatch):
    """Set up a complete environment for testing."""
    env_vars = {
        "MOBIUS_APP_NAME": "Test Mobius",
        "MOBIUS_ENVIRONMENT": "test",
        "MOBIUS_DEBUG": "true",
        "MOBIUS_HOST": "127.0.0.1",
        "MOBIUS_PORT": "8080",
        "MOBIUS_DATABASE__URL": "postgresql://test:password@localhost/test_db",
        "MOBIUS_DATABASE__POOL_SIZE": "5",
        "MOBIUS_DATABASE__MAX_OVERFLOW": "10",
        "MOBIUS_REDIS__URL": "redis://localhost:6379/1",
        "MOBIUS_REDIS__TTL": "7200",
        "MOBIUS_SECURITY__SECRET_KEY": "super-secret-test-key",
        "MOBIUS_SECURITY__JWT_ALGORITHM": "HS512",
        "MOBIUS_SECURITY__JWT_EXPIRATION_MINUTES": "60",
        "MOBIUS_SECURITY__ALLOWED_ORIGINS": '["http://localhost:3000","http://localhost:5173"]',
        "MOBIUS_ENABLE_ANALYTICS": "false",
        "MOBIUS_ENABLE_CACHE": "false",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


class TestConfigurationLoading:
    """Test configuration loading from environment variables."""
    
    def test_load_minimal_config(self, clean_env, basic_env):
        """Test loading configuration with minimal required settings."""
        settings = Settings()
        
        # Check defaults are applied
        assert settings.app_name == "Mobius Context Platform"
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.port == 8000
        
        # Check required fields are loaded
        assert settings.database.url == "postgresql://user:pass@localhost/mobius"
        assert settings.security.secret_key.get_secret_value() == "test-secret-key-123"
    
    def test_load_full_config(self, clean_env, full_env):
        """Test loading configuration with all environment variables set."""
        settings = Settings()
        
        # Application settings
        assert settings.app_name == "Test Mobius"
        assert settings.environment == "test"
        assert settings.debug is True
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        
        # Database settings
        assert settings.database.url == "postgresql://test:password@localhost/test_db"
        assert settings.database.pool_size == 5
        assert settings.database.max_overflow == 10
        
        # Redis settings
        assert settings.redis.url == "redis://localhost:6379/1"
        assert settings.redis.ttl == 7200
        
        # Security settings
        assert settings.security.secret_key.get_secret_value() == "super-secret-test-key"
        assert settings.security.jwt_algorithm == "HS512"
        assert settings.security.jwt_expiration_minutes == 60
        assert settings.security.allowed_origins == ["http://localhost:3000", "http://localhost:5173"]
        
        # Feature flags
        assert settings.enable_analytics is False
        assert settings.enable_cache is False
    
    def test_env_var_override_defaults(self, clean_env, basic_env, monkeypatch):
        """Test that environment variables override default values."""
        # First load with defaults
        settings1 = Settings()
        assert settings1.port == 8000
        
        # Set env var and reload
        monkeypatch.setenv("MOBIUS_PORT", "9000")
        settings2 = Settings()
        assert settings2.port == 9000
    
    def test_missing_required_fields(self, clean_env):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        # Should have errors for missing database URL and security secret key
        assert len(errors) >= 2
        
        error_fields = [error["loc"] for error in errors]
        assert ("database", "url") in error_fields
        assert ("security", "secret_key") in error_fields
    
    def test_nested_env_delimiter(self, clean_env, monkeypatch):
        """Test nested configuration using double underscore delimiter."""
        monkeypatch.setenv("MOBIUS_DATABASE__URL", "postgresql://nested@localhost/db")
        monkeypatch.setenv("MOBIUS_DATABASE__POOL_SIZE", "15")
        monkeypatch.setenv("MOBIUS_SECURITY__SECRET_KEY", "nested-secret")
        
        settings = Settings()
        assert settings.database.url == "postgresql://nested@localhost/db"
        assert settings.database.pool_size == 15
    
    def test_case_insensitive_env_vars(self, clean_env, basic_env, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("mobius_port", "7777")
        monkeypatch.setenv("MOBIUS_HOST", "0.0.0.0")
        
        settings = Settings()
        assert settings.port == 7777
        assert settings.host == "0.0.0.0"


class TestConfigurationValidation:
    """Test configuration value validation."""
    
    def test_database_url_validation(self, clean_env, monkeypatch):
        """Test database URL format validation."""
        monkeypatch.setenv("MOBIUS_SECURITY__SECRET_KEY", "test-key")
        
        # Valid PostgreSQL URL
        monkeypatch.setenv("MOBIUS_DATABASE__URL", "postgresql://user:pass@host/db")
        settings = Settings()
        assert settings.database.url == "postgresql://user:pass@host/db"
        
        # Valid SQLite URL
        monkeypatch.setenv("MOBIUS_DATABASE__URL", "sqlite:///path/to/db.sqlite")
        settings = Settings()
        assert settings.database.url == "sqlite:///path/to/db.sqlite"
        
        # Invalid URL
        monkeypatch.setenv("MOBIUS_DATABASE__URL", "mysql://user:pass@host/db")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any("Invalid database URL format" in str(error) for error in errors)
    
    def test_port_range_validation(self, clean_env, basic_env, monkeypatch):
        """Test port number range validation."""
        # Valid port
        monkeypatch.setenv("MOBIUS_PORT", "3000")
        settings = Settings()
        assert settings.port == 3000
        
        # Port too low
        monkeypatch.setenv("MOBIUS_PORT", "0")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(error) for error in errors)
        
        # Port too high
        monkeypatch.setenv("MOBIUS_PORT", "70000")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 65535" in str(error) for error in errors)
    
    def test_environment_validation(self, clean_env, basic_env, monkeypatch):
        """Test environment value validation."""
        # Valid environments
        for env in ["development", "staging", "production", "test"]:
            monkeypatch.setenv("MOBIUS_ENVIRONMENT", env)
            settings = Settings()
            assert settings.environment == env
        
        # Invalid environment
        monkeypatch.setenv("MOBIUS_ENVIRONMENT", "invalid")
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any("Environment must be one of" in str(error) for error in errors)
    
    def test_boolean_parsing(self, clean_env, basic_env, monkeypatch):
        """Test boolean value parsing from environment variables."""
        # True values
        for value in ["true", "True", "TRUE", "1", "yes", "Yes"]:
            monkeypatch.setenv("MOBIUS_DEBUG", value)
            settings = Settings()
            assert settings.debug is True
        
        # False values
        for value in ["false", "False", "FALSE", "0", "no", "No"]:
            monkeypatch.setenv("MOBIUS_DEBUG", value)
            settings = Settings()
            assert settings.debug is False
    
    def test_json_list_parsing(self, clean_env, basic_env, monkeypatch):
        """Test parsing JSON lists from environment variables."""
        monkeypatch.setenv("MOBIUS_SECURITY__ALLOWED_ORIGINS", '["http://example.com","https://app.example.com"]')
        settings = Settings()
        assert settings.security.allowed_origins == ["http://example.com", "https://app.example.com"]
        
        # Invalid JSON should raise error
        monkeypatch.setenv("MOBIUS_SECURITY__ALLOWED_ORIGINS", "not-json")
        with pytest.raises(ValidationError):
            Settings()


class TestEnvironmentConfigurations:
    """Test different environment-specific configurations."""
    
    def test_development_config(self, clean_env, basic_env, monkeypatch):
        """Test development environment configuration."""
        monkeypatch.setenv("MOBIUS_ENVIRONMENT", "development")
        settings = Settings()
        
        assert settings.environment == "development"
        # In a real implementation, debug might be auto-enabled for development
        # This is just an example of environment-specific testing
    
    def test_production_config(self, clean_env, basic_env, monkeypatch):
        """Test production environment configuration."""
        monkeypatch.setenv("MOBIUS_ENVIRONMENT", "production")
        monkeypatch.setenv("MOBIUS_DEBUG", "true")  # Try to enable debug
        
        settings = Settings()
        assert settings.environment == "production"
        # In a real implementation, you might want to force debug=False in production
        # regardless of the env var setting
    
    def test_test_config(self, clean_env, monkeypatch):
        """Test test environment configuration."""
        # Test environment might use different database
        monkeypatch.setenv("MOBIUS_ENVIRONMENT", "test")
        monkeypatch.setenv("MOBIUS_DATABASE__URL", "sqlite:///test.db")
        monkeypatch.setenv("MOBIUS_SECURITY__SECRET_KEY", "test-only-key")
        
        settings = Settings()
        assert settings.environment == "test"
        assert "test" in settings.database.url


class TestSensitiveDataHandling:
    """Test handling of sensitive configuration data."""
    
    def test_secret_fields_not_exposed(self, clean_env, basic_env):
        """Test that secret fields are not exposed in string representations."""
        settings = Settings()
        
        # Secret value should be accessible via get_secret_value()
        assert settings.security.secret_key.get_secret_value() == "test-secret-key-123"
        
        # But not in string representation
        secret_str = str(settings.security.secret_key)
        assert "test-secret-key-123" not in secret_str
        assert "**********" in secret_str or "SecretStr" in secret_str
    
    def test_settings_repr_safe(self, clean_env, basic_env):
        """Test that Settings repr doesn't expose sensitive data."""
        settings = Settings()
        repr_str = repr(settings)
        
        # Should not contain secret values
        assert "test-secret-key-123" not in repr_str
        assert settings.database.url not in repr_str
        
        # Should contain safe identifying information
        assert "Settings" in repr_str
        assert "environment=" in repr_str
    
    def test_no_secrets_in_validation_errors(self, clean_env, monkeypatch):
        """Test that validation errors don't expose secret values."""
        monkeypatch.setenv("MOBIUS_DATABASE__URL", "invalid-url")
        monkeypatch.setenv("MOBIUS_SECURITY__SECRET_KEY", "super-secret-value")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        error_str = str(exc_info.value)
        # Secret value should not appear in error messages
        assert "super-secret-value" not in error_str
    
    def test_dict_export_with_secrets(self, clean_env, basic_env):
        """Test exporting settings to dict with secret handling."""
        settings = Settings()
        
        # Standard dict export should not expose secrets
        settings_dict = settings.model_dump()
        assert isinstance(settings_dict["security"]["secret_key"], SecretStr)
        
        # Explicit mode to show secrets (use with caution)
        settings_dict_with_secrets = settings.model_dump(mode="python")
        # SecretStr should still be SecretStr object, not raw value
        assert isinstance(settings_dict_with_secrets["security"]["secret_key"], SecretStr)


class TestConfigurationEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_string_env_vars(self, clean_env, basic_env, monkeypatch):
        """Test handling of empty string environment variables."""
        monkeypatch.setenv("MOBIUS_APP_NAME", "")
        
        settings = Settings()
        # Empty string should be treated as empty, not use default
        assert settings.app_name == ""
    
    def test_extra_env_vars_ignored(self, clean_env, basic_env, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("MOBIUS_UNKNOWN_FIELD", "should-be-ignored")
        monkeypatch.setenv("MOBIUS_ANOTHER_UNKNOWN", "also-ignored")
        
        # Should not raise an error
        settings = Settings()
        assert not hasattr(settings, "unknown_field")
        assert not hasattr(settings, "another_unknown")
    
    def test_env_file_loading(self, clean_env, tmp_path, monkeypatch):
        """Test loading configuration from .env file."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("""
MOBIUS_DATABASE__URL=postgresql://envfile:pass@localhost/db
MOBIUS_SECURITY__SECRET_KEY=env-file-secret
MOBIUS_PORT=4321
""")
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        settings = Settings()
        assert settings.database.url == "postgresql://envfile:pass@localhost/db"
        assert settings.port == 4321
    
    def test_env_var_precedence(self, clean_env, tmp_path, monkeypatch):
        """Test that environment variables take precedence over .env file."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("""
MOBIUS_PORT=1111
MOBIUS_DATABASE__URL=postgresql://file:pass@localhost/db
MOBIUS_SECURITY__SECRET_KEY=file-secret
""")
        
        monkeypatch.chdir(tmp_path)
        
        # Set environment variable that should override .env
        monkeypatch.setenv("MOBIUS_PORT", "2222")
        
        settings = Settings()
        assert settings.port == 2222  # From env var, not .env file
        assert settings.database.url == "postgresql://file:pass@localhost/db"  # From .env file
    
    def test_invalid_json_in_env_var(self, clean_env, basic_env, monkeypatch):
        """Test handling of invalid JSON in environment variables."""
        monkeypatch.setenv("MOBIUS_SECURITY__ALLOWED_ORIGINS", "[invalid json")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any("json" in str(error).lower() for error in errors)
    
    def test_numeric_string_conversion(self, clean_env, basic_env, monkeypatch):
        """Test conversion of numeric strings from environment variables."""
        monkeypatch.setenv("MOBIUS_DATABASE__POOL_SIZE", "25")
        monkeypatch.setenv("MOBIUS_REDIS__TTL", "1800")
        
        settings = Settings()
        assert settings.database.pool_size == 25
        assert isinstance(settings.database.pool_size, int)
        assert settings.redis.ttl == 1800
        assert isinstance(settings.redis.ttl, int)
    
    def test_settings_immutability(self, clean_env, basic_env):
        """Test that settings instances are immutable by default."""
        settings = Settings()
        
        # Pydantic models are immutable by default in v2
        with pytest.raises(AttributeError):
            settings.port = 9999


# Module-level tests
def test_settings_can_be_imported():
    """Test that Settings class can be imported."""
    from app.core.config import Settings
    assert Settings is not None


def test_settings_singleton_pattern():
    """Test that settings can be used in a singleton pattern."""
    from app.core.config import get_settings, reset_settings
    
    # Reset to ensure clean state
    reset_settings()
    
    # Get settings twice
    settings1 = get_settings()
    settings2 = get_settings()
    
    # Should be the same instance
    assert settings1 is settings2
    
    # Reset and get again
    reset_settings()
    settings3 = get_settings()
    
    # Should be a different instance after reset
    assert settings1 is not settings3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])