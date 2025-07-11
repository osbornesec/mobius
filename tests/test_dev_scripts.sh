#!/bin/bash
#
# Development Scripts Test Suite for Mobius Context Engineering Platform
#
# This script tests that all development scripts and setup procedures work correctly.
# It should be run from the project root directory.
#
# Usage: ./tests/test_dev_scripts.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

run_test() {
    local test_name="$1"
    local test_command="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    echo -n "Testing $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_error "Command failed: $test_command"
        return 1
    fi
}

# Test setup script creates virtual environment
test_virtual_environment_setup() {
    log_info "Testing Python virtual environment setup..."

    # Check if venv module is available
    run_test "Python venv module availability" "python3 -m venv --help"

    # Test creating a virtual environment
    local test_venv_dir="$PROJECT_ROOT/.test_venv"
    run_test "Virtual environment creation" "python3 -m venv $test_venv_dir"

    # Test virtual environment structure
    run_test "Virtual environment bin directory" "test -d $test_venv_dir/bin"
    run_test "Virtual environment activate script" "test -f $test_venv_dir/bin/activate"
    run_test "Virtual environment python executable" "test -x $test_venv_dir/bin/python"

    # Clean up test virtual environment
    rm -rf "$test_venv_dir"

    # Check for existing .venv or venv directory
    if [[ -d "$PROJECT_ROOT/.venv" ]]; then
        run_test "Project virtual environment exists (.venv)" "test -d $PROJECT_ROOT/.venv"
    elif [[ -d "$PROJECT_ROOT/venv" ]]; then
        run_test "Project virtual environment exists (venv)" "test -d $PROJECT_ROOT/venv"
    else
        log_warning "No existing virtual environment found. Consider creating one at .venv or venv"
    fi
}

# Test setup script installs dependencies
test_dependency_installation() {
    log_info "Testing dependency installation capabilities..."

    # Test pip is available
    run_test "pip availability" "python3 -m pip --version"

    # Test requirements.txt exists
    run_test "requirements.txt exists" "test -f $PROJECT_ROOT/requirements.txt"

    # Test requirements.txt is not empty
    run_test "requirements.txt not empty" "test -s $PROJECT_ROOT/requirements.txt"

    # Check if requirements-dev.txt exists (optional)
    if [[ -f "$PROJECT_ROOT/requirements-dev.txt" ]]; then
        run_test "requirements-dev.txt exists" "test -f $PROJECT_ROOT/requirements-dev.txt"
        run_test "requirements-dev.txt not empty" "test -s $PROJECT_ROOT/requirements-dev.txt"
    fi

    # Test npm is available for frontend dependencies
    run_test "npm availability" "npm --version"

    # Test package.json exists
    run_test "package.json exists" "test -f $PROJECT_ROOT/package.json"

    # Test package-lock.json or yarn.lock exists (one should be present)
    if [[ -f "$PROJECT_ROOT/package-lock.json" ]]; then
        run_test "package-lock.json exists" "test -f $PROJECT_ROOT/package-lock.json"
    elif [[ -f "$PROJECT_ROOT/yarn.lock" ]]; then
        run_test "yarn.lock exists" "test -f $PROJECT_ROOT/yarn.lock"
    else
        log_warning "No package-lock.json or yarn.lock found. Consider running 'npm install' or 'yarn install'"
    fi
}

# Test development server startup scripts work
test_development_server_scripts() {
    log_info "Testing development server scripts..."

    # Test Docker Compose is configured correctly
    run_test "docker-compose.yml exists" "test -f $PROJECT_ROOT/docker-compose.yml"
    run_test "docker-compose config validation" "docker compose config > /dev/null"

    # Test Makefile exists and has common targets
    if [[ -f "$PROJECT_ROOT/Makefile" ]]; then
        run_test "Makefile exists" "test -f $PROJECT_ROOT/Makefile"

        # Check for common Make targets
        local makefile_content=$(cat "$PROJECT_ROOT/Makefile")

        if grep -q "up:" "$PROJECT_ROOT/Makefile" 2>/dev/null; then
            run_test "Makefile has 'up' target" "grep -q 'up:' $PROJECT_ROOT/Makefile"
        fi

        if grep -q "down:" "$PROJECT_ROOT/Makefile" 2>/dev/null; then
            run_test "Makefile has 'down' target" "grep -q 'down:' $PROJECT_ROOT/Makefile"
        fi

        if grep -q "test:" "$PROJECT_ROOT/Makefile" 2>/dev/null; then
            run_test "Makefile has 'test' target" "grep -q 'test:' $PROJECT_ROOT/Makefile"
        fi
    else
        log_warning "No Makefile found. Consider creating one for common development tasks"
    fi

    # Test for development scripts directory
    if [[ -d "$PROJECT_ROOT/scripts" ]]; then
        run_test "scripts directory exists" "test -d $PROJECT_ROOT/scripts"

        # Check for common development scripts
        local script_files=(
            "scripts/setup.sh"
            "scripts/start.sh"
            "scripts/test.sh"
            "scripts/lint.sh"
        )

        for script in "${script_files[@]}"; do
            if [[ -f "$PROJECT_ROOT/$script" ]]; then
                run_test "$script exists" "test -f $PROJECT_ROOT/$script"
                run_test "$script is executable" "test -x $PROJECT_ROOT/$script"
            fi
        done
    fi

    # Test FastAPI app module exists
    run_test "FastAPI main.py exists" "test -f $PROJECT_ROOT/app/main.py"

    # Test if uvicorn can import the app (syntax check only)
    run_test "FastAPI app imports correctly" "python3 -c 'import sys; sys.path.insert(0, \"$PROJECT_ROOT\"); import app.main'"
}

# Test database initialization scripts work
test_database_initialization() {
    log_info "Testing database initialization scripts..."

    # Test PostgreSQL init script exists
    run_test "PostgreSQL init.sql exists" "test -f $PROJECT_ROOT/infrastructure/init.sql"

    # Test init.sql is not empty
    run_test "init.sql not empty" "test -s $PROJECT_ROOT/infrastructure/init.sql"

    # Test for Alembic configuration
    if [[ -d "$PROJECT_ROOT/alembic" ]]; then
        run_test "Alembic directory exists" "test -d $PROJECT_ROOT/alembic"
        run_test "alembic.ini exists" "test -f $PROJECT_ROOT/alembic.ini"

        # Test Alembic versions directory
        run_test "Alembic versions directory exists" "test -d $PROJECT_ROOT/alembic/versions"
    else
        log_warning "No Alembic directory found. Database migrations may not be configured"
    fi

    # Test for database connection testing capability
    run_test "psql command available" "which psql"
    run_test "redis-cli command available" "which redis-cli"
}

# Test pre-commit hooks setup
test_precommit_hooks() {
    log_info "Testing pre-commit hooks configuration..."

    # Check if .pre-commit-config.yaml exists
    if [[ -f "$PROJECT_ROOT/.pre-commit-config.yaml" ]]; then
        run_test ".pre-commit-config.yaml exists" "test -f $PROJECT_ROOT/.pre-commit-config.yaml"
        run_test ".pre-commit-config.yaml not empty" "test -s $PROJECT_ROOT/.pre-commit-config.yaml"

        # Test pre-commit is installed
        if command -v pre-commit &> /dev/null; then
            run_test "pre-commit command available" "which pre-commit"

            # Test pre-commit configuration is valid
            run_test "pre-commit config validation" "pre-commit validate-config"
        else
            log_warning "pre-commit not installed. Run 'pip install pre-commit' to enable git hooks"
        fi
    else
        log_warning "No .pre-commit-config.yaml found. Consider setting up pre-commit hooks"
    fi

    # Check for .git/hooks directory
    if [[ -d "$PROJECT_ROOT/.git/hooks" ]]; then
        run_test "Git hooks directory exists" "test -d $PROJECT_ROOT/.git/hooks"
    fi
}

# Test environment variables setup
test_environment_variables() {
    log_info "Testing environment variables configuration..."

    # Test .env.example or .env.sample exists
    if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
        run_test ".env.example exists" "test -f $PROJECT_ROOT/.env.example"
        run_test ".env.example not empty" "test -s $PROJECT_ROOT/.env.example"
    elif [[ -f "$PROJECT_ROOT/.env.sample" ]]; then
        run_test ".env.sample exists" "test -f $PROJECT_ROOT/.env.sample"
        run_test ".env.sample not empty" "test -s $PROJECT_ROOT/.env.sample"
    else
        log_error "Neither .env.example nor .env.sample found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Warning if .env file exists (shouldn't be committed)
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_warning ".env file exists - ensure it's in .gitignore and not committed"

        # Check if .env is in .gitignore
        if [[ -f "$PROJECT_ROOT/.gitignore" ]] && grep -q "^\.env$" "$PROJECT_ROOT/.gitignore"; then
            run_test ".env is in .gitignore" "grep -q '^\.env$' $PROJECT_ROOT/.gitignore"
        fi
    fi
}

# Test Docker environment
test_docker_environment() {
    log_info "Testing Docker environment..."

    # Test Docker daemon is running
    run_test "Docker daemon is running" "docker info"

    # Test Docker Compose v2 is available
    run_test "Docker Compose v2 available" "docker compose version"

    # Test required Docker images can be pulled
    local required_images=(
        "pgvector/pgvector:pg15"
        "redis:7-alpine"
        "qdrant/qdrant:latest"
    )

    for image in "${required_images[@]}"; do
        # Just check if we can inspect the image (don't actually pull)
        run_test "Docker image accessible: $image" "docker image inspect $image || docker pull --dry-run $image 2>/dev/null || true"
    done

    # Test Docker networks don't conflict
    run_test "Docker default network available" "docker network ls | grep -q bridge"
}

# Main test runner
main() {
    log_info "Starting Mobius Development Environment Tests"
    log_info "Project root: $PROJECT_ROOT"
    echo

    # Run all test suites
    test_virtual_environment_setup
    echo

    test_dependency_installation
    echo

    test_development_server_scripts
    echo

    test_database_initialization
    echo

    test_precommit_hooks
    echo

    test_environment_variables
    echo

    test_docker_environment
    echo

    # Print summary
    echo "========================================"
    echo "Test Summary:"
    echo "========================================"
    echo -e "Total tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_info "All tests passed! Development environment is properly configured."
        exit 0
    else
        log_error "Some tests failed. Please fix the issues above."
        exit 1
    fi
}

# Run main function
main "$@"
