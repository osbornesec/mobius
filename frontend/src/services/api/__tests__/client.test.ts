import { describe, it, expect, beforeEach, vi, afterEach, MockedFunction } from 'vitest';
import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import apiClient, { ApiRequestError } from '../config';
import useAuthStore from '@/store/authStore';

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
const mockLocation = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

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

describe('API Client', () => {
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
    mockAxiosInstance = {
      interceptors: {
        request: {
          use: vi.fn((success, error) => {
            requestInterceptor = { success, error };
            return 0;
          }),
        },
        response: {
          use: vi.fn((success, error) => {
            responseInterceptor = { success, error };
            return 0;
          }),
        },
      },
      defaults: {},
    };

    // Mock axios.create to return our mock instance
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockAxiosInstance as any);

    // Re-import to get fresh instance with mocks
    vi.resetModules();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Request Interceptor', () => {
    it('should add auth token to requests when available', async () => {
      const mockToken = 'test-auth-token';
      localStorageMock.getItem.mockReturnValue(mockToken);

      const config: AxiosRequestConfig = {
        headers: {},
        url: '/test',
        method: 'GET',
      };

      // Import fresh to trigger interceptor setup
      await import('../config');

      const result = await requestInterceptor.success(config);

      expect(localStorageMock.getItem).toHaveBeenCalledWith('authToken');
      expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
    });

    it('should not add auth token when not available', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const config: AxiosRequestConfig = {
        headers: {},
        url: '/test',
        method: 'GET',
      };

      // Import fresh to trigger interceptor setup
      await import('../config');

      const result = await requestInterceptor.success(config);

      expect(localStorageMock.getItem).toHaveBeenCalledWith('authToken');
      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should handle request interceptor errors', async () => {
      const error = new Error('Request interceptor error');

      // Import fresh to trigger interceptor setup
      await import('../config');

      await expect(requestInterceptor.error(error)).rejects.toEqual(error);
    });
  });

  describe('Response Interceptor', () => {
    it('should pass through successful responses', async () => {
      const mockResponse: AxiosResponse = {
        data: { message: 'Success' },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as AxiosRequestConfig,
      };

      // Import fresh to trigger interceptor setup
      await import('../config');

      const result = await responseInterceptor.success(mockResponse);

      expect(result).toEqual(mockResponse);
    });

    describe('Error Handling', () => {
      it('should handle timeout errors', async () => {
        const timeoutError = new Error('Timeout') as AxiosError;
        timeoutError.code = 'ECONNABORTED';
        timeoutError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(timeoutError)).rejects.toMatchObject({
          message: 'Request timed out. Please check your connection and try again.',
          code: 'TIMEOUT',
          originalError: timeoutError,
        });
      });

      it('should handle network errors', async () => {
        const networkError = new Error('Network Error') as AxiosError;
        networkError.request = {};
        networkError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(networkError)).rejects.toMatchObject({
          message: 'Network error. Please check your internet connection.',
          code: 'NETWORK_ERROR',
          originalError: networkError,
        });
      });

      it('should handle 401 unauthorized and refresh token', async () => {
        const mockNewToken = 'new-auth-token';
        const mockAuthStore = {
          refreshToken: vi.fn().mockResolvedValue(undefined),
          logout: vi.fn(),
        };
        
        (useAuthStore.getState as MockedFunction<typeof useAuthStore.getState>).mockReturnValue(mockAuthStore as any);
        localStorageMock.getItem.mockReturnValue(mockNewToken);

        const unauthorizedError = new Error('Unauthorized') as AxiosError;
        unauthorizedError.response = {
          status: 401,
          data: {},
          statusText: 'Unauthorized',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        unauthorizedError.config = {
          headers: {},
          url: '/test',
          method: 'GET',
        } as AxiosRequestConfig;

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
        expect(unauthorizedError.config!.headers!.Authorization).toBe(`Bearer ${mockNewToken}`);
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
          config: {} as AxiosRequestConfig,
        };
        unauthorizedError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

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
          config: {} as AxiosRequestConfig,
        };
        unauthorizedError.config = { _retry: true } as AxiosRequestConfig & { _retry?: boolean };

        // Import fresh to trigger interceptor setup
        await import('../config');

        // Should not attempt refresh if already retried
        await expect(responseInterceptor.error(unauthorizedError)).rejects.toEqual(unauthorizedError);

        const mockAuthStore = useAuthStore.getState();
        expect(mockAuthStore.refreshToken).not.toHaveBeenCalled();
      });

      it('should handle 5xx server errors', async () => {
        const serverError = new Error('Server Error') as AxiosError;
        serverError.response = {
          status: 500,
          data: {},
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        serverError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(serverError)).rejects.toMatchObject({
          message: 'Server error. Our team has been notified. Please try again later.',
          code: 'SERVER_ERROR',
          status: 500,
          originalError: serverError,
        });
      });

      it('should handle 4xx client errors with custom message', async () => {
        const clientError = new Error('Client Error') as AxiosError;
        clientError.response = {
          status: 400,
          data: { message: 'Custom error message' },
          statusText: 'Bad Request',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        clientError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(clientError)).rejects.toMatchObject({
          message: 'Custom error message',
          code: 'CLIENT_ERROR',
          status: 400,
          originalError: clientError,
        });
      });

      it('should handle 4xx client errors with detail message', async () => {
        const clientError = new Error('Client Error') as AxiosError;
        clientError.response = {
          status: 422,
          data: { detail: 'Validation error details' },
          statusText: 'Unprocessable Entity',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        clientError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(clientError)).rejects.toMatchObject({
          message: 'Validation error details',
          code: 'CLIENT_ERROR',
          status: 422,
          originalError: clientError,
        });
      });

      it('should handle 4xx client errors with default message', async () => {
        const clientError = new Error('Client Error') as AxiosError;
        clientError.response = {
          status: 404,
          data: {},
          statusText: 'Not Found',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        clientError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(clientError)).rejects.toMatchObject({
          message: 'Invalid request. Please check your input.',
          code: 'CLIENT_ERROR',
          status: 404,
          originalError: clientError,
        });
      });

      it('should handle other errors with response data', async () => {
        const otherError = new Error('Other Error') as AxiosError;
        otherError.response = {
          status: 300,
          data: { message: 'Redirect message' },
          statusText: 'Multiple Choices',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        otherError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(otherError)).rejects.toThrow('Redirect message');
      });

      it('should handle other errors without message', async () => {
        const otherError = new Error('Other Error') as AxiosError;
        otherError.response = {
          status: 300,
          data: {},
          statusText: 'Multiple Choices',
          headers: {},
          config: {} as AxiosRequestConfig,
        };
        otherError.config = {} as AxiosRequestConfig;

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(otherError)).rejects.toThrow('An error occurred');
      });

      it('should handle unknown errors', async () => {
        const unknownError = new Error('Unknown error');

        // Import fresh to trigger interceptor setup
        await import('../config');

        await expect(responseInterceptor.error(unknownError)).rejects.toEqual(unknownError);
      });
    });
  });

  describe('ApiRequestError', () => {
    it('should create error with all properties', () => {
      const originalError = new Error('Original');
      const error = new ApiRequestError('Test error', 'TEST_CODE', 400, originalError);

      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(ApiRequestError);
      expect(error.message).toBe('Test error');
      expect(error.name).toBe('ApiRequestError');
      expect(error.code).toBe('TEST_CODE');
      expect(error.status).toBe(400);
      expect(error.originalError).toBe(originalError);
    });

    it('should create error without optional properties', () => {
      const error = new ApiRequestError('Test error', 'TEST_CODE');

      expect(error.message).toBe('Test error');
      expect(error.code).toBe('TEST_CODE');
      expect(error.status).toBeUndefined();
      expect(error.originalError).toBeUndefined();
    });

    it('should have proper stack trace', () => {
      const error = new ApiRequestError('Test error', 'TEST_CODE');

      expect(error.stack).toBeDefined();
      expect(error.stack).toContain('ApiRequestError');
    });
  });

  describe('API Client Configuration', () => {
    it('should be configured with correct base URL and timeout', async () => {
      // Import fresh to trigger axios.create
      await import('../config');

      expect(axios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8000/api/v1',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });
  });
});