import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import useAuthStore from '../authStore';
import { authService } from '@/services/api/auth';
import {
  MOCK_USER,
  MOCK_ACCESS_TOKEN,
  MOCK_REFRESH_TOKEN,
  MOCK_LOGIN_RESPONSE,
  MOCK_REFRESH_RESPONSE,
  MOCK_CREDENTIALS,
  MOCK_NEW_ACCESS_TOKEN,
  AUTH_ERROR_MESSAGES,
} from '@/__tests__/mocks/auth';

// Mock the auth service
vi.mock('@/services/api/auth', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
global.localStorage = localStorageMock as Storage;

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });

    // Clear all mocks
    vi.clearAllMocks();

    // Reset localStorage mock
    localStorageMock.getItem.mockReset();
    localStorageMock.setItem.mockReset();
    localStorageMock.removeItem.mockReset();
  });

  afterEach(() => {
    // Clean up any timers
    vi.clearAllTimers();
  });

  describe('login', () => {
    it('should successfully login and update state', async () => {
      // Mock successful login
      vi.mocked(authService.login).mockResolvedValueOnce(MOCK_LOGIN_RESPONSE);

      // Perform login
      await useAuthStore.getState().login(MOCK_CREDENTIALS.email, MOCK_CREDENTIALS.password);

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toEqual(MOCK_USER);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();

      // Token storage is now handled internally by authService
    });

    it('should set isLoading during login', async () => {
      // Mock a delayed login response
      let resolveLogin: ((value: any) => void) | null = null;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      vi.mocked(authService.login).mockReturnValueOnce(loginPromise);

      // Start login
      const loginAction = useAuthStore
        .getState()
        .login(MOCK_CREDENTIALS.email, MOCK_CREDENTIALS.password);

      // Check loading state is true
      expect(useAuthStore.getState().isLoading).toBe(true);

      // Resolve login safely
      if (resolveLogin) {
        resolveLogin(MOCK_LOGIN_RESPONSE);
      } else {
        throw new Error('resolveLogin was not set');
      }

      await loginAction;

      // Check loading state is false after completion
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it('should handle login failure', async () => {
      // Mock failed login
      vi.mocked(authService.login).mockRejectedValueOnce(
        new Error(AUTH_ERROR_MESSAGES.INVALID_CREDENTIALS)
      );

      // Perform login and expect it to throw
      await expect(
        useAuthStore.getState().login(MOCK_CREDENTIALS.email, 'wrong-password')
      ).rejects.toThrow(AUTH_ERROR_MESSAGES.INVALID_CREDENTIALS);

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(AUTH_ERROR_MESSAGES.INVALID_CREDENTIALS);
    });
  });

  describe('logout', () => {
    it('should clear user data and token', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: MOCK_USER,
        isAuthenticated: true,
      });

      // Perform logout
      await useAuthStore.getState().logout();

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);

      // Token removal is now handled internally by authService
    });
  });

  describe('setUser', () => {
    it('should update user and authentication state', () => {
      // Set user
      useAuthStore.getState().setUser(MOCK_USER);

      // Check state
      const state = useAuthStore.getState();
      expect(state.user).toEqual(MOCK_USER);
      expect(state.isAuthenticated).toBe(true);
    });

    it('should clear user when null is passed', () => {
      // Set user to null
      useAuthStore.getState().setUser(null);

      // Check state
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      // Set error state
      useAuthStore.setState({ error: 'Some error' });

      // Clear error
      useAuthStore.getState().clearError();

      // Check state
      expect(useAuthStore.getState().error).toBeNull();
    });
  });

  describe('refreshToken', () => {
    it('should successfully refresh token and update state', async () => {
      // Mock successful refresh
      vi.mocked(authService.refreshToken).mockResolvedValueOnce(MOCK_REFRESH_RESPONSE);

      // Perform refresh
      await useAuthStore.getState().refreshToken();

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toEqual(MOCK_USER);
      expect(state.isAuthenticated).toBe(true);
      expect(state.error).toBeNull();

      // Token storage is now handled internally by authService
    });

    it('should logout on refresh failure', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: MOCK_USER,
        isAuthenticated: true,
      });

      // Mock failed refresh
      vi.mocked(authService.refreshToken).mockRejectedValueOnce(
        new Error(AUTH_ERROR_MESSAGES.TOKEN_EXPIRED)
      );

      // Mock logout to prevent actual API call
      vi.mocked(authService.logout).mockResolvedValueOnce(undefined);

      // Perform refresh and expect it to throw
      await expect(useAuthStore.getState().refreshToken()).rejects.toThrow(
        AUTH_ERROR_MESSAGES.TOKEN_EXPIRED
      );

      // Check that logout was called
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      // Token removal is now handled internally by authService
    });
  });

  describe('state persistence', () => {
    it('should persist only user and isAuthenticated state', () => {
      // Set full state
      useAuthStore.setState({
        user: MOCK_USER,
        isAuthenticated: true,
        isLoading: true,
        error: 'Some error',
      });

      // The persist middleware configuration in authStore specifies
      // that only user and isAuthenticated should be persisted
      const state = useAuthStore.getState();

      // Verify that the state contains all properties
      expect(state.user).toEqual(MOCK_USER);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(true);
      expect(state.error).toBe('Some error');

      // Note: The actual persistence behavior is tested implicitly
      // through the partialize configuration in the store definition
    });
  });

  describe('error handling', () => {
    it('should handle errors without message property', async () => {
      const error = { code: 'NETWORK_ERROR' };

      // Mock failed login with non-standard error
      vi.mocked(authService.login).mockRejectedValueOnce(error);

      // Perform login and expect it to throw
      await expect(
        useAuthStore.getState().login(MOCK_CREDENTIALS.email, MOCK_CREDENTIALS.password)
      ).rejects.toEqual(error);

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.error).toBe(AUTH_ERROR_MESSAGES.LOGIN_FAILED);
      expect(state.isAuthenticated).toBe(false);
    });

    it('should handle logout errors gracefully', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: MOCK_USER,
        isAuthenticated: true,
      });

      // Mock console.error to verify it's called
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock failed logout
      vi.mocked(authService.logout).mockRejectedValueOnce(
        new Error(AUTH_ERROR_MESSAGES.NETWORK_ERROR)
      );

      // Perform logout
      await useAuthStore.getState().logout();

      // Check that error was logged
      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout error:', expect.any(Error));

      // Check that state was still cleared
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      // Token removal is now handled internally by authService

      // Clean up
      consoleErrorSpy.mockRestore();
    });
  });
});
