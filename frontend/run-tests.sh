#!/bin/bash

# Run tests for auth store and API client
echo "Running Mobius Frontend Tests..."
echo "================================"

# Run specific test files
echo "Running Auth Store Tests..."
npm test src/store/__tests__/authStore.test.ts

echo -e "\nRunning API Client Tests..."
npm test src/services/api/__tests__/client.test.ts

echo -e "\nRunning All Tests with Coverage..."
npm test -- --coverage