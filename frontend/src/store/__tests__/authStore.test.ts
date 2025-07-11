import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import useAuthStore from '../authStore';
import { authService } from '@/services/api/auth';

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
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      };
      const mockToken = 'mock-token';

      // Mock successful login
      vi.mocked(authService.login).mockResolvedValueOnce({
        user: mockUser,
        token: mockToken,
        refreshToken: 'mock-refresh-token',
      });

      // Perform login
      await useAuthStore.getState().login('test@example.com', 'password');

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();

      // Check localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('authToken', mockToken);
    });

    it('should set isLoading during login', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      };

      // Mock a delayed login response
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      vi.mocked(authService.login).mockReturnValueOnce(loginPromise);

      // Start login
      const loginAction = useAuthStore.getState().login('test@example.com', 'password');

      // Check loading state is true
      expect(useAuthStore.getState().isLoading).toBe(true);

      // Resolve login
      resolveLogin!({
        user: mockUser,
        token: 'mock-token',
        refreshToken: 'mock-refresh-token',
      });

      await loginAction;

      // Check loading state is false after completion
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';

      // Mock failed login
      vi.mocked(authService.login).mockRejectedValueOnce(new Error(errorMessage));

      // Perform login and expect it to throw
      await expect(
        useAuthStore.getState().login('test@example.com', 'wrong-password')
      ).rejects.toThrow(errorMessage);

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(errorMessage);
    });
  });

  describe('logout', () => {
    it('should clear user data and token', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          role: 'user',
          createdAt: '2024-01-01',
          updatedAt: '2024-01-01',
        },
        isAuthenticated: true,
      });

      // Perform logout
      await useAuthStore.getState().logout();

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);

      // Check localStorage
      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
    });
  });

  describe('setUser', () => {
    it('should update user and authentication state', () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      };

      // Set user
      useAuthStore.getState().setUser(mockUser);

      // Check state
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
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
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      };
      const newToken = 'new-mock-token';

      // Mock successful refresh
      vi.mocked(authService.refreshToken).mockResolvedValueOnce({
        user: mockUser,
        token: newToken,
        refreshToken: 'new-refresh-token',
      });

      // Perform refresh
      await useAuthStore.getState().refreshToken();

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.error).toBeNull();

      // Check localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('authToken', newToken);
    });

    it('should logout on refresh failure', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          role: 'user',
          createdAt: '2024-01-01',
          updatedAt: '2024-01-01',
        },
        isAuthenticated: true,
      });

      // Mock failed refresh
      vi.mocked(authService.refreshToken).mockRejectedValueOnce(new Error('Token expired'));

      // Mock logout to prevent actual API call
      vi.mocked(authService.logout).mockResolvedValueOnce(undefined);

      // Perform refresh and expect it to throw
      await expect(useAuthStore.getState().refreshToken()).rejects.toThrow('Token expired');

      // Check that logout was called
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
    });
  });

  describe('state persistence', () => {
    it('should persist only user and isAuthenticated state', () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      };

      // Set full state
      useAuthStore.setState({
        user: mockUser,
        isAuthenticated: true,
        isLoading: true,
        error: 'Some error',
      });

      // Get the persist options from the store
      const persistOptions = (useAuthStore as any).persist;
      const partializedState = persistOptions.partialize(useAuthStore.getState());

      // Check that only user and isAuthenticated are persisted
      expect(partializedState).toEqual({
        user: mockUser,
        isAuthenticated: true,
      });
      expect(partializedState).not.toHaveProperty('isLoading');
      expect(partializedState).not.toHaveProperty('error');
    });
  });

  describe('error handling', () => {
    it('should handle errors without message property', async () => {
      const error = { code: 'NETWORK_ERROR' };

      // Mock failed login with non-standard error
      vi.mocked(authService.login).mockRejectedValueOnce(error);

      // Perform login and expect it to throw
      await expect(useAuthStore.getState().login('test@example.com', 'password')).rejects.toEqual(
        error
      );

      // Check state updates
      const state = useAuthStore.getState();
      expect(state.error).toBe('Login failed');
      expect(state.isAuthenticated).toBe(false);
    });

    it('should handle logout errors gracefully', async () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          role: 'user',
          createdAt: '2024-01-01',
          updatedAt: '2024-01-01',
        },
        isAuthenticated: true,
      });

      // Mock console.error to verify it's called
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock failed logout
      vi.mocked(authService.logout).mockRejectedValueOnce(new Error('Network error'));

      // Perform logout
      await useAuthStore.getState().logout();

      // Check that error was logged
      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout error:', expect.any(Error));

      // Check that state was still cleared
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');

      // Clean up
      consoleErrorSpy.mockRestore();
    });
  });
});
