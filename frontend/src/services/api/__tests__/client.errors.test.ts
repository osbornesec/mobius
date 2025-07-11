import { describe, it, expect, beforeEach, vi, MockedFunction } from 'vitest';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { ApiRequestError } from '../config';
import { createMockAxiosInstance, createMockConfig } from './testHelpers';

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

describe('API Client Error Handling', () => {
  let responseInterceptor: any;

  beforeEach(async () => {
    // Reset mocks
    vi.clearAllMocks();

    // Create mock axios instance
    const { mockInstance, getInterceptors } = createMockAxiosInstance();
    
    // Mock axios.create to return our mock instance
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockInstance as any);

    // Re-import to get fresh instance with mocks
    vi.resetModules();
    
    // Import and get interceptors
    await import('../config');
    const interceptors = getInterceptors();
    responseInterceptor = interceptors.responseInterceptor;
  });

  describe('Network and Timeout Errors', () => {
    it('should handle timeout errors', async () => {
      const timeoutError = new Error('Timeout') as AxiosError;
      timeoutError.code = 'ECONNABORTED';
      timeoutError.config = createMockConfig();

      await expect(responseInterceptor.error(timeoutError)).rejects.toMatchObject({
        message: 'Request timed out. Please check your connection and try again.',
        code: 'TIMEOUT',
        originalError: timeoutError,
      });
    });

    it('should handle network errors', async () => {
      const networkError = new Error('Network Error') as AxiosError;
      networkError.request = {};
      networkError.config = createMockConfig();

      await expect(responseInterceptor.error(networkError)).rejects.toMatchObject({
        message: 'Network error. Please check your internet connection.',
        code: 'NETWORK_ERROR',
        originalError: networkError,
      });
    });
  });

  describe('Server Errors', () => {
    it('should handle 5xx server errors', async () => {
      const serverError = new Error('Server Error') as AxiosError;
      serverError.response = {
        status: 500,
        data: {},
        statusText: 'Internal Server Error',
        headers: {},
        config: createMockConfig(),
      };
      serverError.config = createMockConfig();

      await expect(responseInterceptor.error(serverError)).rejects.toMatchObject({
        message: 'Server error. Our team has been notified. Please try again later.',
        code: 'SERVER_ERROR',
        status: 500,
        originalError: serverError,
      });
    });

    it('should handle 503 service unavailable', async () => {
      const serverError = new Error('Service Unavailable') as AxiosError;
      serverError.response = {
        status: 503,
        data: {},
        statusText: 'Service Unavailable',
        headers: {},
        config: createMockConfig(),
      };
      serverError.config = createMockConfig();

      await expect(responseInterceptor.error(serverError)).rejects.toMatchObject({
        message: 'Server error. Our team has been notified. Please try again later.',
        code: 'SERVER_ERROR',
        status: 503,
        originalError: serverError,
      });
    });
  });

  describe('Client Errors', () => {
    it('should handle 4xx client errors with custom message', async () => {
      const clientError = new Error('Client Error') as AxiosError;
      clientError.response = {
        status: 400,
        data: { message: 'Custom error message' },
        statusText: 'Bad Request',
        headers: {},
        config: createMockConfig(),
      };
      clientError.config = createMockConfig();

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
        config: createMockConfig(),
      };
      clientError.config = createMockConfig();

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
        config: createMockConfig(),
      };
      clientError.config = createMockConfig();

      await expect(responseInterceptor.error(clientError)).rejects.toMatchObject({
        message: 'Invalid request. Please check your input.',
        code: 'CLIENT_ERROR',
        status: 404,
        originalError: clientError,
      });
    });
  });

  describe('Other Response Errors', () => {
    it('should handle other errors with response data', async () => {
      const otherError = new Error('Other Error') as AxiosError;
      otherError.response = {
        status: 300,
        data: { message: 'Redirect message' },
        statusText: 'Multiple Choices',
        headers: {},
        config: createMockConfig(),
      };
      otherError.config = createMockConfig();

      await expect(responseInterceptor.error(otherError)).rejects.toThrow('Redirect message');
    });

    it('should handle other errors without message', async () => {
      const otherError = new Error('Other Error') as AxiosError;
      otherError.response = {
        status: 300,
        data: {},
        statusText: 'Multiple Choices',
        headers: {},
        config: createMockConfig(),
      };
      otherError.config = createMockConfig();

      await expect(responseInterceptor.error(otherError)).rejects.toThrow('An error occurred');
    });
  });

  describe('Unknown Errors', () => {
    it('should handle unknown errors', async () => {
      const unknownError = new Error('Unknown error');

      await expect(responseInterceptor.error(unknownError)).rejects.toEqual(unknownError);
    });
  });

  describe('ApiRequestError Class', () => {
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
});