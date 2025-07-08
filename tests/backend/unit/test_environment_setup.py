"""
Environment setup validation tests for the Mobius Context Engineering Platform.

This module tests that all required development tools and configurations
are properly set up for the Mobius project.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
import yaml


class TestEnvironmentSetup:
    """Test suite for validating the development environment setup."""

    @pytest.fixture(scope="class")
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent.parent

    def _run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """
        Run a shell command and return the exit code, stdout, and stderr.
        
        Args:
            command: List of command arguments
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError:
            return 1, "", f"Command not found: {command[0]}"

    def _parse_version(self, version_string: str) -> Optional[Tuple[int, ...]]:
        """
        Parse a version string into a tuple of integers.
        
        Args:
            version_string: Version string like "1.2.3"
            
        Returns:
            Tuple of version numbers or None if parsing fails
        """
        # Extract version number pattern (e.g., 1.2.3)
        match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', version_string)
        if match:
            groups = match.groups()
            return tuple(int(g) if g else 0 for g in groups)
        return None

    def test_required_tools_installed(self):
        """Verify all required development tools are available."""
        # Test Docker version >= 20.10
        exit_code, stdout, stderr = self._run_command(["docker", "--version"])
        assert exit_code == 0, f"Docker not installed or not accessible: {stderr}"
        
        docker_version = self._parse_version(stdout)
        assert docker_version is not None, f"Could not parse Docker version from: {stdout}"
        assert docker_version >= (20, 10), f"Docker version {docker_version} is less than required 20.10"

        # Test Docker Compose version >= 2.0
        # Try both 'docker compose' and 'docker-compose' commands
        exit_code, stdout, stderr = self._run_command(["docker", "compose", "version"])
        if exit_code != 0:
            exit_code, stdout, stderr = self._run_command(["docker-compose", "--version"])
        
        assert exit_code == 0, f"Docker Compose not installed or not accessible: {stderr}"
        
        compose_version = self._parse_version(stdout)
        assert compose_version is not None, f"Could not parse Docker Compose version from: {stdout}"
        assert compose_version >= (2, 0), f"Docker Compose version {compose_version} is less than required 2.0"

        # Test Python version >= 3.11
        python_version = sys.version_info
        assert python_version.major == 3 and python_version.minor >= 11, \
            f"Python version {python_version.major}.{python_version.minor} is less than required 3.11"

        # Test Node.js version >= 18.0
        exit_code, stdout, stderr = self._run_command(["node", "--version"])
        assert exit_code == 0, f"Node.js not installed or not accessible: {stderr}"
        
        node_version = self._parse_version(stdout)
        assert node_version is not None, f"Could not parse Node.js version from: {stdout}"
        assert node_version >= (18, 0), f"Node.js version {node_version} is less than required 18.0"

        # Test PostgreSQL client tools (optional for Docker-only development)
        exit_code, stdout, stderr = self._run_command(["psql", "--version"])
        if exit_code == 0:
            psql_version = self._parse_version(stdout)
            if psql_version is not None:
                assert psql_version >= (15,), f"PostgreSQL version {psql_version} is less than required 15"
        # If psql is not available, that's okay - developers can use Docker containers

        # Test Redis client tools (optional for Docker-only development)
        exit_code, stdout, stderr = self._run_command(["redis-cli", "--version"])
        if exit_code == 0:
            redis_version = self._parse_version(stdout)
            if redis_version is not None:
                assert redis_version >= (7,), f"Redis version {redis_version} is less than required 7"
        # If redis-cli is not available, that's okay - developers can use Docker containers

    def test_docker_compose_configuration(self, project_root: Path):
        """Verify docker-compose.yml is valid and services are defined."""
        docker_compose_path = project_root / "docker-compose.yml"
        assert docker_compose_path.exists(), f"docker-compose.yml not found at {docker_compose_path}"

        # Test docker-compose config is valid YAML
        with open(docker_compose_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.yml: {e}")

        assert isinstance(config, dict), "docker-compose.yml should contain a dictionary"
        assert "services" in config, "docker-compose.yml must have a 'services' section"

        # Test all required services are defined
        required_services = ["postgres", "redis", "qdrant", "backend", "frontend"]
        services = config.get("services", {})
        
        for service in required_services:
            assert service in services, f"Required service '{service}' not found in docker-compose.yml"

        # Test port mappings don't conflict
        used_ports: Dict[int, str] = {}
        for service_name, service_config in services.items():
            if "ports" in service_config:
                for port_mapping in service_config["ports"]:
                    # Parse port mapping (e.g., "8000:8000" or "0.0.0.0:8000:8000")
                    parts = str(port_mapping).split(":")
                    host_port = int(parts[-2] if len(parts) > 2 else parts[0])
                    
                    if host_port in used_ports:
                        pytest.fail(
                            f"Port conflict: {host_port} used by both "
                            f"'{used_ports[host_port]}' and '{service_name}'"
                        )
                    used_ports[host_port] = service_name

        # Test volume mounts are correctly configured
        expected_volumes = {
            "postgres": ["postgres_data", "./infrastructure/init.sql"],
            "redis": ["redis_data"],
            "qdrant": ["qdrant_data"],
            "backend": ["./backend"],  # Backend volume mount
            "frontend": ["./frontend", "/app/node_modules"]  # Frontend is correctly in frontend/ subdirectory
        }

        for service_name, expected_vols in expected_volumes.items():
            service_config = services.get(service_name, {})
            volumes = service_config.get("volumes", [])
            
            for expected_vol in expected_vols:
                # Check if expected volume is present (could be in different formats)
                found = any(
                    expected_vol in str(vol) or str(vol).startswith(f"{expected_vol}:")
                    for vol in volumes
                )
                assert found, (
                    f"Expected volume '{expected_vol}' not found "
                    f"in service '{service_name}' volumes: {volumes}"
                )

        # Verify environment variables are set for services
        expected_env_vars = {
            "postgres": ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"],
            "backend": ["DATABASE_URL", "REDIS_URL", "QDRANT_URL", "ENVIRONMENT"],
            "frontend": ["REACT_APP_API_URL"]
        }

        for service_name, expected_vars in expected_env_vars.items():
            service_config = services.get(service_name, {})
            env_config = service_config.get("environment", {})
            
            # Environment can be a dict or a list
            if isinstance(env_config, list):
                env_keys = [var.split("=")[0] for var in env_config]
            else:
                env_keys = list(env_config.keys())
            
            for expected_var in expected_vars:
                assert expected_var in env_keys, (
                    f"Expected environment variable '{expected_var}' "
                    f"not found in service '{service_name}'"
                )

        # Verify health checks are defined for critical services
        services_requiring_health_checks = ["postgres", "redis", "qdrant"]
        for service_name in services_requiring_health_checks:
            service_config = services.get(service_name, {})
            assert "healthcheck" in service_config, (
                f"Service '{service_name}' should have a healthcheck defined"
            )
            
            healthcheck = service_config["healthcheck"]
            assert "test" in healthcheck, f"Healthcheck for '{service_name}' must have a 'test' command"
            assert "interval" in healthcheck, f"Healthcheck for '{service_name}' must have an 'interval'"
            assert "timeout" in healthcheck, f"Healthcheck for '{service_name}' must have a 'timeout'"
            assert "retries" in healthcheck, f"Healthcheck for '{service_name}' must have 'retries'"

        # Verify dependencies are correctly set
        assert "depends_on" in services["backend"], "Backend service should have dependencies"
        backend_deps = services["backend"]["depends_on"]
        
        # Handle both list and dict formats for depends_on
        if isinstance(backend_deps, dict):
            assert all(
                dep in backend_deps for dep in ["postgres", "redis", "qdrant"]
            ), "Backend should depend on postgres, redis, and qdrant"
            
            # Verify condition is set to service_healthy
            for dep in ["postgres", "redis", "qdrant"]:
                assert backend_deps[dep].get("condition") == "service_healthy", (
                    f"Backend dependency '{dep}' should wait for service_healthy condition"
                )
        else:
            assert all(
                dep in backend_deps for dep in ["postgres", "redis", "qdrant"]
            ), "Backend should depend on postgres, redis, and qdrant"

        assert "depends_on" in services["frontend"], "Frontend service should have dependencies"
        assert "backend" in services["frontend"]["depends_on"], "Frontend should depend on backend"

    def test_environment_variables(self, project_root: Path):
        """Verify .env.example contains all required variables."""
        # Check for .env.example or .env.sample
        env_example_path = project_root / ".env.example"
        if not env_example_path.exists():
            env_example_path = project_root / ".env.sample"
        
        assert env_example_path.exists(), (
            f"Neither .env.example nor .env.sample found at {project_root}"
        )

        # Read and parse environment variables
        env_vars = {}
        with open(env_example_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        # Test all required env vars are documented
        required_vars = [
            # API Configuration
            "FASTAPI_ENV",
            "API_HOST",
            "API_PORT",
            "API_VERSION",
            
            # Database Configuration
            "DATABASE_URL",
            "REDIS_URL",
            
            # Vector Database Configuration
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "PINECONE_API_KEY",
            "PINECONE_ENVIRONMENT",
            
            # Storage Configuration
            "S3_BUCKET_NAME",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_REGION",
            
            # Security Configuration
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "JWT_EXPIRATION_HOURS",
            
            # OAuth Configuration
            "OAUTH_CLIENT_ID",
            "OAUTH_CLIENT_SECRET",
            
            # AI Integration Keys
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            
            # GitHub Integration
            "GITHUB_APP_ID",
            "GITHUB_PRIVATE_KEY",
            
            # Monitoring
            "SENTRY_DSN",
            
            # Frontend Configuration
            "REACT_APP_API_URL",
            "REACT_APP_WS_URL"
        ]

        for var in required_vars:
            assert var in env_vars, f"Required environment variable '{var}' not found in {env_example_path.name}"

        # Test default values are provided where appropriate
        vars_with_defaults = {
            "FASTAPI_ENV": "development",
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
            "API_VERSION": "v1",
            "JWT_ALGORITHM": "HS256",
            "JWT_EXPIRATION_HOURS": "24",
            "AWS_REGION": "us-east-1",
            "REACT_APP_API_URL": "http://localhost:8000/api/v1",
            "REACT_APP_WS_URL": "ws://localhost:8000/ws"
        }

        for var, expected_default in vars_with_defaults.items():
            assert env_vars.get(var) == expected_default, (
                f"Variable '{var}' should have default value '{expected_default}', "
                f"but has '{env_vars.get(var)}'"
            )

        # Test sensitive values are not committed (should be placeholder values)
        sensitive_vars = [
            "DATABASE_URL",
            "QDRANT_API_KEY",
            "PINECONE_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "JWT_SECRET_KEY",
            "OAUTH_CLIENT_ID",
            "OAUTH_CLIENT_SECRET",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GITHUB_APP_ID",
            "GITHUB_PRIVATE_KEY",
            "SENTRY_DSN"
        ]

        placeholder_patterns = [
            "your_", "YOUR_", "xxx", "XXX", "placeholder", "PLACEHOLDER",
            "example", "EXAMPLE", "secret", "SECRET", "key", "KEY",
            "user:password", "localhost"
        ]

        for var in sensitive_vars:
            value = env_vars.get(var, "")
            # Check if the value contains any placeholder pattern
            has_placeholder = any(pattern in value for pattern in placeholder_patterns)
            assert has_placeholder, (
                f"Sensitive variable '{var}' should have a placeholder value, "
                f"not '{value}'"
            )


class TestProjectStructure:
    """Test suite for validating project structure and configuration files."""

    @pytest.fixture(scope="class")
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent.parent

    def test_required_directories_exist(self, project_root: Path):
        """Verify all required project directories exist."""
        required_dirs = [
            # Backend directories
            "app",
            "app/agents",
            "app/api",
            "app/core",
            "app/models",
            "app/services",
            "app/storage",
            "app/utils",
            
            # Test directories
            "tests",
            "tests/backend",
            "tests/backend/unit",
            "tests/backend/integration",
            "tests/backend/e2e",
            "tests/frontend",
            
            # Infrastructure and deployment
            "infrastructure",
            "docker",
            "scripts",
            "docs",
            
            # Frontend directories
            "frontend",
            "frontend/src",
            "src",  # Additional frontend source (for components, etc.)
            "public",  # Frontend public assets
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists() and full_path.is_dir(), (
                f"Required directory '{dir_path}' does not exist"
            )

    def test_required_files_exist(self, project_root: Path):
        """Verify all required configuration files exist."""
        required_files = [
            # Root level configuration files
            "docker-compose.yml",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "Makefile",
            
            # Backend files
            "app/main.py",
            
            # Infrastructure files
            "infrastructure/init.sql",
            
            # Frontend files (in frontend/ subdirectory)
            "frontend/package.json",
            "frontend/vite.config.ts",
            "frontend/tsconfig.json",
        ]

        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists() and full_path.is_file(), (
                f"Required file '{file_path}' does not exist"
            )
        
        # Special handling for .env.sample/.env.example
        env_sample = project_root / ".env.sample"
        env_example = project_root / ".env.example"
        assert env_sample.exists() or env_example.exists(), (
            "Neither .env.sample nor .env.example exists"
        )

    def test_python_configuration_files(self, project_root: Path):
        """Verify Python configuration files are properly set up."""
        # Check pyproject.toml
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(pyproject_path, 'rb') as f:
            pyproject_data = tomllib.load(f)

        # Verify project metadata
        assert "project" in pyproject_data or "tool" in pyproject_data, (
            "pyproject.toml should contain project metadata"
        )

        # Check requirements.txt
        requirements_path = project_root / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt not found"

        with open(requirements_path, 'r') as f:
            requirements = f.read().strip()
            assert requirements, "requirements.txt should not be empty"

        # Verify key production dependencies are listed
        key_dependencies = [
            "fastapi",
            "pydantic",
            "sqlalchemy",
            "alembic",
            "redis",
            "uvicorn"
        ]

        requirements_lower = requirements.lower()
        for dep in key_dependencies:
            assert dep in requirements_lower, (
                f"Key dependency '{dep}' not found in requirements.txt"
            )
        
        # Check for development dependencies in requirements-dev.txt if it exists
        dev_requirements_path = project_root / "requirements-dev.txt"
        if dev_requirements_path.exists():
            with open(dev_requirements_path, 'r') as f:
                dev_requirements = f.read().strip().lower()
                # pytest should be in dev requirements
                assert "pytest" in dev_requirements, (
                    "pytest should be found in requirements-dev.txt"
                )

    def test_nodejs_configuration_files(self, project_root: Path):
        """Verify Node.js configuration files are properly set up."""
        # Check frontend package.json (where the actual frontend config should be)
        frontend_package_json_path = project_root / "frontend" / "package.json"
        assert frontend_package_json_path.exists(), "frontend/package.json not found"

        with open(frontend_package_json_path, 'r') as f:
            try:
                package_data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in frontend/package.json: {e}")

        # Verify package.json structure
        assert "name" in package_data, "frontend/package.json must have a 'name' field"
        assert "version" in package_data, "frontend/package.json must have a 'version' field"
        assert "scripts" in package_data, "frontend/package.json must have a 'scripts' section"

        # Verify essential scripts for a modern React/Vite frontend
        scripts = package_data.get("scripts", {})
        essential_scripts = ["dev", "build", "test"]
        
        for script in essential_scripts:
            assert script in scripts, f"Essential script '{script}' not found in frontend/package.json"

        # Verify dependencies section exists
        assert "dependencies" in package_data or "devDependencies" in package_data, (
            "frontend/package.json must have dependencies or devDependencies"
        )
        
        # Verify key React/frontend dependencies are present
        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        all_deps = {**dependencies, **dev_dependencies}
        
        key_frontend_deps = ["react", "react-dom", "typescript", "vite"]
        for dep in key_frontend_deps:
            assert any(dep in dep_name for dep_name in all_deps.keys()), (
                f"Key frontend dependency '{dep}' not found in frontend/package.json"
            )

    def test_project_structure_organization(self, project_root: Path):
        """
        Verify the project follows proper backend/frontend separation.
        
        This test validates that:
        - Backend files (Python, FastAPI) are at root level or in app/ directory
        - Frontend files (React, TypeScript) are in frontend/ subdirectory
        - Frontend source code is properly organized in frontend/src/
        - Root package.json (if exists) is either empty or workspace configuration
        """
        # Backend files should be at root level or in app/ directory
        backend_files = [
            "app/main.py",
            "requirements.txt", 
            "pyproject.toml",
            "alembic.ini" if (project_root / "alembic.ini").exists() else None
        ]
        
        # Filter out None values
        backend_files = [f for f in backend_files if f is not None]
        
        for file_path in backend_files:
            full_path = project_root / file_path
            if file_path == "alembic.ini":
                # alembic.ini is optional but if it exists, should be at root
                if full_path.exists():
                    assert full_path.is_file(), f"Backend file '{file_path}' should exist at root level"
            else:
                assert full_path.exists() and full_path.is_file(), (
                    f"Backend file '{file_path}' should exist at root level or in app/"
                )
        
        # Frontend files should be in frontend/ subdirectory
        frontend_files = [
            "frontend/package.json",
            "frontend/vite.config.ts",
            "frontend/tsconfig.json",
        ]
        
        for file_path in frontend_files:
            full_path = project_root / file_path
            assert full_path.exists() and full_path.is_file(), (
                f"Frontend file '{file_path}' should exist in frontend/ subdirectory"
            )
        
        # Verify frontend source code is properly organized
        frontend_src_path = project_root / "frontend" / "src"
        assert frontend_src_path.exists() and frontend_src_path.is_dir(), (
            "Frontend source code should be in frontend/src/ directory"
        )
        
        # Additional src/ directory at root (for shared components, etc.) should also exist
        root_src_path = project_root / "src"
        assert root_src_path.exists() and root_src_path.is_dir(), (
            "Root src/ directory should exist for shared components"
        )
        
        # Verify that package.json at root (if exists) is either empty or workspace config
        root_package_json = project_root / "package.json"
        if root_package_json.exists():
            # Should be either empty or contain workspace configuration
            with open(root_package_json, 'r') as f:
                content = f.read().strip()
                if content:  # If not empty, should be valid JSON
                    f.seek(0)  # Reset file pointer to beginning
                    try:
                        root_package_data = json.load(f)
                        # If it has content, it should be a workspace root or monorepo config
                        if root_package_data:
                            # Could be workspace config, but shouldn't duplicate frontend functionality
                            assert "workspaces" in root_package_data or "private" in root_package_data, (
                                "Root package.json should be workspace configuration, not duplicate frontend config"
                            )
                    except json.JSONDecodeError:
                        pytest.fail("Root package.json contains invalid JSON")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])