#!/bin/bash

# Enable strict error handling
# -e: Exit immediately if any command exits with non-zero status
# -u: Treat unset variables as an error and exit
# -o pipefail: Return value of a pipeline is the status of the last command to exit with non-zero status
set -euo pipefail

# Run tests for auth store and API client
echo "Running Mobius Frontend Tests..."
echo "================================"

# Run specific test files
# Using npx vitest run to ensure proper argument passing
echo "Running Auth Store Tests..."
if [ -f "src/store/__tests__/authStore.test.ts" ]; then
    npx vitest run src/store/__tests__/authStore.test.ts
else
    echo "Warning: authStore.test.ts not found, skipping..."
fi

echo -e "\nRunning API Client Tests..."
# Run all client-related tests in the api directory
if [ -d "src/services/api/__tests__" ]; then
    npx vitest run "src/services/api/__tests__/*.test.ts"
else
    echo "Warning: API test directory not found, skipping..."
fi

echo -e "\nRunning All Tests with Coverage..."
# Use npx vitest run with coverage flag for consistent behavior
npx vitest run --coverage