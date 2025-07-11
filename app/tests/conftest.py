"""
Pytest configuration for Mobius test suite.

This module contains shared fixtures and configuration for all tests.
"""

import os
import sys
from pathlib import Path

import pytest

# Add the app directory to Python path for imports
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring external API keys"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test characteristics."""
    for item in items:
        # Add markers based on test file names
        if "pinecone" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.requires_api_key)

        # Add slow marker to certain test methods
        if any(
            name in item.nodeid
            for name in ["test_batch_operations", "test_index_creation"]
        ):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def check_environment():
    """Check that required environment variables are set."""
    required_vars = []
    optional_vars = ["PINECONE_API_KEY", "QDRANT_API_KEY", "OPENAI_API_KEY"]

    missing_required = [var for var in required_vars if not os.environ.get(var)]
    if missing_required:
        pytest.fail(
            f"Required environment variables not set: {', '.join(missing_required)}"
        )

    # Log optional variables status
    for var in optional_vars:
        if os.environ.get(var):
            print(f"✓ {var} is set")
        else:
            print(f"⚠ {var} is not set (some tests may be skipped)")

    yield


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to easily mock environment variables in tests."""

    def _mock_env(**kwargs):
        for key, value in kwargs.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)

    return _mock_env
