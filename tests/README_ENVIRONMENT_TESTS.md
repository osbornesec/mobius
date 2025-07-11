# Environment Setup Tests

This directory contains comprehensive tests for validating the Mobius development environment setup.

## Test Files

### 1. `backend/unit/test_environment_setup.py`
Python-based pytest tests that validate:
- Required development tools and their versions (Docker, Docker Compose, Python, Node.js, PostgreSQL, Redis)
- Docker Compose configuration validity
- Environment variables documentation
- Project structure and configuration files

### 2. `test_dev_scripts.sh`
Shell script that tests:
- Python virtual environment setup capabilities
- Dependency installation readiness
- Development server scripts
- Database initialization scripts
- Pre-commit hooks configuration
- Docker environment readiness

## Running the Tests

### Prerequisites
Before running these tests, ensure you have:
1. Python 3.11+ installed
2. Docker and Docker Compose installed
3. Node.js 18+ installed
4. PostgreSQL and Redis client tools installed

### Running Python Tests

First, create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install the test dependencies:
```bash
pip install pytest pyyaml
```

Run the environment setup tests:
```bash
# From project root
python -m pytest tests/backend/unit/test_environment_setup.py -v

# Or run specific test classes
python -m pytest tests/backend/unit/test_environment_setup.py::TestEnvironmentSetup -v
python -m pytest tests/backend/unit/test_environment_setup.py::TestProjectStructure -v
```

### Running Shell Script Tests

The shell script can be run directly:
```bash
# From project root
./tests/test_dev_scripts.sh
```

## Understanding Test Results

### Python Tests Output
The pytest tests will show:
- ✓ PASSED: Requirement is met
- ✗ FAILED: Requirement is not met (with details on what's wrong)

Common failures and solutions:
- **Tool version mismatch**: Update the tool to the required version
- **Missing configuration files**: Create the required files from templates
- **Invalid docker-compose.yml**: Fix YAML syntax or service configuration

### Shell Script Output
The shell script uses colored output:
- 🟢 **[INFO]** Green: Informational messages
- 🟡 **[WARNING]** Yellow: Non-critical issues that should be addressed
- 🔴 **[ERROR]** Red: Critical issues that must be fixed
- **PASSED/FAILED**: Individual test results

## Fixing Common Issues

### 1. Python Version
If you have Python 3.12+ instead of 3.11:
- The tests accept Python 3.11 or higher
- Update `pyproject.toml` to specify `python = "^3.11"`

### 2. Missing Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Docker Compose Version
If using Docker Compose v1:
```bash
# Update to Docker Compose v2
docker compose version  # Should show 2.x.x
```

### 4. Missing Environment File
```bash
cp .env.sample .env
# Edit .env with your actual values
```

### 5. Dependencies Not Installed
```bash
# Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Node.js dependencies
npm install
```

## Continuous Integration

These tests should be run in CI/CD pipelines to ensure:
1. New developers can set up the environment successfully
2. Configuration changes don't break the development setup
3. All required tools remain compatible

Example GitHub Actions workflow:
```yaml
name: Environment Setup Tests
on: [push, pull_request]

jobs:
  test-environment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          pip install pytest pyyaml
          python -m pytest tests/backend/unit/test_environment_setup.py -v
      - run: ./tests/test_dev_scripts.sh
```

## Extending the Tests

To add new environment requirements:

1. **For Python tests**: Add new test methods to the appropriate class in `test_environment_setup.py`
2. **For shell tests**: Add new test functions to `test_dev_scripts.sh`

Example:
```python
def test_new_tool_installed(self):
    """Verify new tool is installed."""
    exit_code, stdout, stderr = self._run_command(["new-tool", "--version"])
    assert exit_code == 0, f"New tool not installed: {stderr}"
```
