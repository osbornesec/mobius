import { describe, it, expect, beforeEach, vi, afterEach, MockedFunction } from 'vitest';
import axios, { AxiosError } from 'axios';
import apiClient from '../config';
import useAuthStore from '@/store/authStore';
import {
  createLocalStorageMock,
  createLocationMock,
  createMockAxiosInstance,
  mockAuthToken,
  mockNewAuthToken,
  createMockConfig,
} from './testHelpers';

// Mock axios
vi.mock('axios');

// Mock auth store
vi.mock('@/store/authStore', () => ({
  default: {
    getState: vi.fn(() => ({
      refreshToken: vi.fn(),
      logout: vi.fn(),
    })),
  },
}));

// Mock window.location
const mockLocation = createLocationMock();
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock localStorage
const localStorageMock = createLocalStorageMock();
global.localStorage = localStorageMock;

describe('API Client Interceptors', () => {
  let mockAxiosInstance: any;
  let requestInterceptor: any;
  let responseInterceptor: any;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    mockLocation.href = '';

    // Reset localStorage mock
    localStorageMock.getItem.mockReset();
    localStorageMock.setItem.mockReset();
    localStorageMock.removeItem.mockReset();

    // Create mock axios instance
    const { mockInstance, getInterceptors } = createMockAxiosInstance();
    mockAxiosInstance = mockInstance;

    // Mock axios.create to return our mock instance
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockAxiosInstance as any);

    // Re-import to get fresh instance with mocks
    vi.resetModules();

    // Extract interceptors after import
    const setupInterceptors = async () => {
      await import('../config');
      const interceptors = getInterceptors();
      requestInterceptor = interceptors.requestInterceptor;
      responseInterceptor = interceptors.responseInterceptor;
    };

    return setupInterceptors();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Request Interceptor', () => {
    it('should add auth token to requests when available', async () => {
      localStorageMock.getItem.mockReturnValue(mockAuthToken);

      const config = createMockConfig();
      const result = await requestInterceptor.success(config);

      expect(localStorageMock.getItem).toHaveBeenCalledWith('authToken');
      expect(result.headers?.Authorization).toBe(`Bearer ${mockAuthToken}`);
    });

    it('should not add auth token when not available', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const config = createMockConfig();
      const result = await requestInterceptor.success(config);

      expect(localStorageMock.getItem).toHaveBeenCalledWith('authToken');
      expect(result.headers?.Authorization).toBeUndefined();
    });

    it('should handle request interceptor errors', async () => {
      const error = new Error('Request interceptor error');

      await expect(requestInterceptor.error(error)).rejects.toEqual(error);
    });
  });

  describe('Response Interceptor', () => {
    it('should pass through successful responses', async () => {
      const mockResponse = {
        data: { message: 'Success' },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: createMockConfig(),
      };

      const result = await responseInterceptor.success(mockResponse);

      expect(result).toEqual(mockResponse);
    });

    describe('401 Unauthorized Handling', () => {
      it('should handle 401 unauthorized and refresh token', async () => {
        const mockAuthStore = {
          refreshToken: vi.fn().mockResolvedValue(undefined),
          logout: vi.fn(),
        };

        (useAuthStore.getState as MockedFunction<typeof useAuthStore.getState>).mockReturnValue(mockAuthStore as any);
        localStorageMock.getItem.mockReturnValue(mockNewAuthToken);

        const unauthorizedError = new Error('Unauthorized') as AxiosError;
        unauthorizedError.response = {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: createMockConfig(),
        };
        unauthorizedError.config = createMockConfig();

        // Mock the retry request
        mockAxiosInstance.mockResolvedValue({
          data: { message: 'Success after refresh' },
          status: 200,
        });

        // Import fresh to trigger interceptor setup
        const { default: client } = await import('../config');
        Object.assign(mockAxiosInstance, client);

        const result = await responseInterceptor.error(unauthorizedError);

        expect(mockAuthStore.refreshToken).toHaveBeenCalled();
        expect(unauthorizedError.config?.headers?.Authorization).toBe(`Bearer ${mockNewAuthToken}`);
        expect(mockAxiosInstance).toHaveBeenCalledWith(unauthorizedError.config);
      });

      it('should logout on 401 when refresh fails', async () => {
        const mockAuthStore = {
          refreshToken: vi.fn().mockRejectedValue(new Error('Refresh failed')),
          logout: vi.fn(),
        };

        (useAuthStore.getState as MockedFunction<typeof useAuthStore.getState>).mockReturnValue(mockAuthStore as any);

        const unauthorizedError = new Error('Unauthorized') as AxiosError;
        unauthorizedError.response = {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: createMockConfig(),
        };
        unauthorizedError.config = createMockConfig();

        await expect(responseInterceptor.error(unauthorizedError)).rejects.toEqual(
          new Error('Refresh failed')
        );

        expect(mockAuthStore.refreshToken).toHaveBeenCalled();
        expect(mockAuthStore.logout).toHaveBeenCalled();
        expect(mockLocation.href).toBe('/login');
      });

      it('should not retry 401 if already retried', async () => {
        const unauthorizedError = new Error('Unauthorized') as AxiosError;
        unauthorizedError.response = {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: createMockConfig(),
        };
        unauthorizedError.config = { ...createMockConfig(), _retry: true } as any;

        // Should not attempt refresh if already retried
        await expect(responseInterceptor.error(unauthorizedError)).rejects.toEqual(unauthorizedError);

        const mockAuthStore = useAuthStore.getState();
        expect(mockAuthStore.refreshToken).not.toHaveBeenCalled();
      });
    });
  });
});
