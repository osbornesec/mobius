#!/bin/bash
# Production configuration validation script
# This script checks for critical production environment variables

# Enable strict error handling
# -e: Exit immediately if any command exits with non-zero status
# -u: Treat unset variables as an error and exit
# -o pipefail: Return value of a pipeline is the status of the last command to exit with non-zero status
set -euo pipefail

# Function to check if a variable is set and not a placeholder
check_variable() {
    local var_name=$1
    local var_value=$2
    local is_critical=${3:-true}
    
    if [ -z "$var_value" ]; then
        echo "ERROR: $var_name is not set"
        if [ "$is_critical" = true ]; then
            exit 1
        fi
    elif [[ "$var_value" == "PLACEHOLDER_"* ]]; then
        echo "WARNING: $var_name is using a placeholder value: $var_value"
        echo "This MUST be replaced with a proper value in production!"
        if [ "$is_critical" = true ]; then
            exit 1
        fi
    else
        echo "✓ $var_name is configured"
    fi
}

echo "Checking production configuration..."
echo "=================================="

# Check critical security variables
check_variable "MOBIUS_SECURITY__SECRET_KEY" "${MOBIUS_SECURITY__SECRET_KEY:-}" true

# Check database configuration
check_variable "POSTGRES_USER" "${POSTGRES_USER:-}" true
check_variable "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD:-}" true

# Check Redis configuration
check_variable "REDIS_PASSWORD" "${REDIS_PASSWORD:-}" true

# Check Qdrant configuration
check_variable "QDRANT_API_KEY" "${QDRANT_API_KEY:-}" true

# Check allowed origins
check_variable "MOBIUS_ALLOWED_ORIGINS" "${MOBIUS_ALLOWED_ORIGINS:-}" true

echo "=================================="
echo "Configuration check complete!"

# Execute the actual command passed to the container
exec "$@"