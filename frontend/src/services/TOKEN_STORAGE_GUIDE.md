# Token Storage Abstraction Guide

## Overview

The token storage system has been refactored to provide a cleaner abstraction layer that improves testability and maintainability. Instead of directly accessing `localStorage` throughout the codebase, all token operations now go through a centralized token storage service.

## Architecture

### Core Components

1. **TokenStorage Interface** (`/services/api/auth.ts`)
   - Defines the contract for token storage operations
   - Methods: `getAccessToken()`, `getRefreshToken()`, `setTokens()`, `clearTokens()`

2. **DefaultTokenStorage Implementation** (`/services/api/auth.ts`)
   - Default implementation using the existing Storage utility
   - Handles all localStorage operations with proper error handling

3. **Shared Token Storage Instance** (`/services/tokenStorage.ts`)
   - Singleton instance used across the application
   - Ensures consistency in token management
   - Provides convenience methods for direct access

4. **AuthService Integration**
   - Accepts a `TokenStorage` instance via constructor
   - All token operations delegated to the storage abstraction
   - Tokens automatically stored/cleared during login/logout/refresh operations

## Usage Examples

### Basic Usage (Application Code)

```typescript
import { authService } from '@/services/api/auth';
import { getAccessToken } from '@/services/tokenStorage';

// Login - tokens are automatically stored
const response = await authService.login('user@example.com', 'password');

// Get current access token
const token = getAccessToken();

// Refresh token - can pass explicit token or use stored one
await authService.refreshToken(); // Uses stored refresh token
await authService.refreshToken('explicit-refresh-token'); // Uses provided token

// Logout - tokens are automatically cleared
await authService.logout();
```

### Testing

```typescript
import { AuthService, TokenStorage } from '@/services/api/auth';

// Create a mock token storage for testing
class MockTokenStorage implements TokenStorage {
  private tokens: { access?: string; refresh?: string } = {};

  getAccessToken(): string | null {
    return this.tokens.access || null;
  }

  getRefreshToken(): string | null {
    return this.tokens.refresh || null;
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.tokens.access = accessToken;
    this.tokens.refresh = refreshToken;
  }

  clearTokens(): void {
    this.tokens = {};
  }
}

// Use in tests
const mockStorage = new MockTokenStorage();
const authService = new AuthService({ tokenStorage: mockStorage });

// Test login behavior
await authService.login('test@example.com', 'password');
expect(mockStorage.getAccessToken()).toBe('expected-token');
```

## Migration Notes

### Changed Files

1. **`/services/api/auth.ts`**
   - Added `TokenStorage` interface and `DefaultTokenStorage` implementation
   - `AuthService` now accepts token storage via constructor
   - All token operations delegated to storage abstraction

2. **`/services/api/config.ts`**
   - Updated to use `getAccessToken()` from shared token storage
   - No longer directly accesses `localStorage`

3. **`/store/authStore.ts`**
   - Removed direct token storage operations
   - Token management now handled entirely by `authService`

4. **`/services/tokenStorage.ts`** (New)
   - Provides shared token storage instance
   - Exports convenience methods for token access

### Breaking Changes

- `authService.refreshToken()` now optionally accepts a refresh token parameter
- Direct `localStorage` access for tokens should be replaced with token storage methods
- Test code that mocks `localStorage` should now mock `TokenStorage` interface

### Benefits

1. **Improved Testability**: Easy to mock token storage for unit tests
2. **Centralized Token Management**: All token operations go through a single service
3. **Better Error Handling**: Storage errors are properly caught and handled
4. **Flexibility**: Easy to swap storage mechanisms (e.g., sessionStorage, in-memory, etc.)
5. **Type Safety**: Full TypeScript support with proper interfaces

## Best Practices

1. **Never access localStorage directly for tokens** - Always use the token storage abstraction
2. **Use the shared instance** - Import from `/services/tokenStorage` for consistency
3. **Handle storage errors** - The storage layer may throw `StorageError` exceptions
4. **Test with mocks** - Use `MockTokenStorage` in tests instead of mocking localStorage

## Future Enhancements

The abstraction layer makes it easy to add:
- Token encryption before storage
- Token expiration tracking
- Multiple token storage strategies
- Token rotation policies
- Secure token storage for mobile/desktop apps
