import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AuthService, TokenStorage } from '../auth';
import apiClient from '../config';
import {
  MOCK_USER,
  MOCK_ACCESS_TOKEN,
  MOCK_REFRESH_TOKEN,
  MOCK_NEW_ACCESS_TOKEN,
  MOCK_CREDENTIALS,
  MOCK_REGISTRATION_DATA,
  AUTH_ERROR_MESSAGES,
} from '@/__tests__/mocks/auth';

// Mock the API client
vi.mock('../config', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
  },
  createRequest: vi.fn((options) => options),
}));

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

  // Helper method for tests to check token state
  getTokens() {
    return { ...this.tokens };
  }
}

describe('AuthService', () => {
  let authService: AuthService;
  let mockTokenStorage: MockTokenStorage;

  beforeEach(() => {
    vi.clearAllMocks();
    mockTokenStorage = new MockTokenStorage();
    authService = new AuthService({ tokenStorage: mockTokenStorage });
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const mockResponse = {
        data: {
          data: {
            user: MOCK_USER,
            token: MOCK_ACCESS_TOKEN,
            refreshToken: MOCK_REFRESH_TOKEN,
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await authService.login(MOCK_CREDENTIALS.email, MOCK_CREDENTIALS.password);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/auth/login',
        MOCK_CREDENTIALS,
        expect.objectContaining({ operationType: 'QUICK' })
      );

      expect(result).toEqual(mockResponse.data.data);

      // Verify tokens were stored
      const tokens = mockTokenStorage.getTokens();
      expect(tokens.access).toBe(MOCK_ACCESS_TOKEN);
      expect(tokens.refresh).toBe(MOCK_REFRESH_TOKEN);
    });

    it('should handle login failure', async () => {
      const error = new Error(AUTH_ERROR_MESSAGES.INVALID_CREDENTIALS);
      vi.mocked(apiClient.post).mockRejectedValueOnce(error);

      await expect(authService.login(MOCK_CREDENTIALS.email, 'wrong-password')).rejects.toThrow(
        AUTH_ERROR_MESSAGES.INVALID_CREDENTIALS
      );

      // Verify no tokens were stored
      const tokens = mockTokenStorage.getTokens();
      expect(tokens.access).toBeUndefined();
      expect(tokens.refresh).toBeUndefined();
    });
  });

  describe('refreshToken', () => {
    it('should refresh token with provided refresh token', async () => {
      const mockResponse = {
        data: {
          data: {
            user: MOCK_USER,
            token: MOCK_NEW_ACCESS_TOKEN,
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await authService.refreshToken(MOCK_REFRESH_TOKEN);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/auth/refresh',
        { refreshToken: MOCK_REFRESH_TOKEN },
        expect.objectContaining({ operationType: 'QUICK' })
      );

      expect(result).toEqual(mockResponse.data.data);
    });

    it('should refresh token from storage when not provided', async () => {
      // Set up token storage with existing refresh token
      mockTokenStorage.setTokens('old-access-token', MOCK_REFRESH_TOKEN);

      const mockResponse = {
        data: {
          data: {
            user: MOCK_USER,
            token: MOCK_NEW_ACCESS_TOKEN,
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await authService.refreshToken();

      expect(apiClient.post).toHaveBeenCalledWith(
        '/auth/refresh',
        { refreshToken: MOCK_REFRESH_TOKEN },
        expect.objectContaining({ operationType: 'QUICK' })
      );

      // Verify new access token was stored
      expect(mockTokenStorage.getAccessToken()).toBe(MOCK_NEW_ACCESS_TOKEN);
      expect(mockTokenStorage.getRefreshToken()).toBe(MOCK_REFRESH_TOKEN);
    });

    it('should throw error when no refresh token available', async () => {
      // Ensure no refresh token in storage
      mockTokenStorage.clearTokens();

      await expect(authService.refreshToken()).rejects.toThrow(
        AUTH_ERROR_MESSAGES.NO_REFRESH_TOKEN
      );
    });
  });

  describe('logout', () => {
    it('should logout and clear tokens', async () => {
      // Set up initial tokens
      mockTokenStorage.setTokens(MOCK_ACCESS_TOKEN, MOCK_REFRESH_TOKEN);

      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} });

      await authService.logout();

      expect(apiClient.post).toHaveBeenCalledWith(
        '/auth/logout',
        {},
        expect.objectContaining({ operationType: 'QUICK' })
      );

      // Verify tokens were cleared
      const tokens = mockTokenStorage.getTokens();
      expect(tokens.access).toBeUndefined();
      expect(tokens.refresh).toBeUndefined();
    });
  });

  describe('register', () => {
    it('should register successfully and store tokens', async () => {
      const newUser = {
        id: '2',
        email: MOCK_REGISTRATION_DATA.email,
        name: MOCK_REGISTRATION_DATA.name,
        role: 'user' as const,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      };

      const mockResponse = {
        data: {
          data: {
            user: newUser,
            token: MOCK_ACCESS_TOKEN,
            refreshToken: MOCK_REFRESH_TOKEN,
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await authService.register(MOCK_REGISTRATION_DATA);

      expect(apiClient.post).toHaveBeenCalledWith('/auth/register', MOCK_REGISTRATION_DATA);

      expect(result).toEqual(mockResponse.data.data);

      // Verify tokens were stored
      const tokens = mockTokenStorage.getTokens();
      expect(tokens.access).toBe(MOCK_ACCESS_TOKEN);
      expect(tokens.refresh).toBe(MOCK_REFRESH_TOKEN);
    });
  });

  describe('getTokenStorage', () => {
    it('should return the token storage instance', () => {
      const storage = authService.getTokenStorage();
      expect(storage).toBe(mockTokenStorage);
    });
  });
});
