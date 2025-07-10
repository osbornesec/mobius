import { describe, it, expect, beforeEach, vi } from 'vitest';
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
});