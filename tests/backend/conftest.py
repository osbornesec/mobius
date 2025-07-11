"""
Shared fixtures for backend tests.

This module provides common fixtures that can be used across all backend tests,
following pytest best practices for fixture organization and reusability.
"""

from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """
    Get the project root directory.

    This fixture is session-scoped to avoid repeated path calculations
    and provides a consistent base path for all tests.

    Returns:
        Path: The absolute path to the project root directory
    """
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def app_directory(project_root: Path) -> Path:
    """
    Get the app directory path.

    Args:
        project_root: The project root directory fixture

    Returns:
        Path: The absolute path to the app directory
    """
    return project_root / "app"


@pytest.fixture(scope="session")
def frontend_directory(project_root: Path) -> Path:
    """
    Get the frontend directory path.

    Args:
        project_root: The project root directory fixture

    Returns:
        Path: The absolute path to the frontend directory
    """
    return project_root / "frontend"


@pytest.fixture(scope="session")
def tests_directory(project_root: Path) -> Path:
    """
    Get the tests directory path.

    Args:
        project_root: The project root directory fixture

    Returns:
        Path: The absolute path to the tests directory
    """
    return project_root / "tests"
