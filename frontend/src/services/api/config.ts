import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import useAuthStore from '@/store/authStore';
import { getTimeoutForEndpoint, RETRY_CONFIG } from './timeouts';
import {
  isRetryableError,
  getRetryState,
  clearRetryState,
  sleep,
  calculateBackoffDelay,
  enhanceErrorMessage,
  formatRetryMessage,
} from './retry';
import { getAccessToken } from '@/services/tokenStorage';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const IS_DEVELOPMENT = import.meta.env.DEV;

// Custom error class for API errors
export class ApiRequestError extends Error {
  code: string;
  status?: number;
  originalError?: unknown;

  constructor(message: string, code: string, status?: number, originalError?: unknown) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
    this.status = status;
    this.originalError = originalError;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiRequestError);
    }
  }
}

// Create axios instance with dynamic timeout
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add AbortController support for better cancellation
export const createAbortController = () => new AbortController();

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token to requests using token storage abstraction
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Set dynamic timeout based on endpoint
    if (!config.timeout) {
      const endpoint = config.url || '';
      const method = config.method?.toUpperCase() || 'GET';
      config.timeout = getTimeoutForEndpoint(endpoint, method);
    }

    // Add request timing in development
    if (IS_DEVELOPMENT) {
      config.metadata = { startTime: Date.now() };
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Create a navigation helper that will be set by the app
let navigateToLogin: (() => void) | null = null;

export const setNavigateToLogin = (navigate: () => void) => {
  navigateToLogin = navigate;
};

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Log request timing in development
    if (IS_DEVELOPMENT && response.config.metadata?.startTime) {
      const duration = Date.now() - response.config.metadata.startTime;
      console.log(
        `[API] ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`
      );
    }

    // Clear retry state on success
    clearRetryState(response.config);

    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Get retry state
    const retryState = getRetryState(originalRequest);

    // Handle retryable errors
    if (isRetryableError(error) && retryState.retryCount < RETRY_CONFIG.maxRetries) {
      retryState.retryCount++;

      // Calculate backoff delay
      const delay = calculateBackoffDelay(retryState.retryCount - 1);

      if (IS_DEVELOPMENT) {
        console.log(
          `[API] ${formatRetryMessage(retryState.retryCount, RETRY_CONFIG.maxRetries, delay)}`
        );
      }

      // Wait before retrying
      await sleep(delay);

      // Retry the request
      return apiClient(originalRequest);
    }

    // Clear retry state after max retries
    clearRetryState(originalRequest);

    // Handle timeout errors after retries
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      const enhancedMessage = enhanceErrorMessage(error);
      return Promise.reject(new ApiRequestError(enhancedMessage, 'TIMEOUT', 408, error));
    }

    // Handle network errors
    if (!error.response && error.request) {
      return Promise.reject(
        new ApiRequestError(
          'Network error. Please check your internet connection.',
          'NETWORK_ERROR',
          undefined,
          error
        )
      );
    }

    // Handle 401 Unauthorized
    // Skip retry logic for refresh endpoint to prevent infinite recursion
    const isRefreshEndpoint = originalRequest.url?.includes('/auth/refresh');

    if (error.response?.status === 401 && !originalRequest._retry && !isRefreshEndpoint) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        await useAuthStore.getState().refreshToken();

        // Retry original request with new token from token storage
        const token = getAccessToken();
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        useAuthStore.getState().logout();

        // Use router navigation if available, otherwise fallback to window.location
        if (navigateToLogin) {
          navigateToLogin();
        } else {
          window.location.href = '/login';
        }

        return Promise.reject(refreshError);
      }
    }

    // Handle server errors (5xx) with user-friendly message
    if (error.response?.status && error.response.status >= 500) {
      return Promise.reject(
        new ApiRequestError(
          'Server error. Our team has been notified. Please try again later.',
          'SERVER_ERROR',
          error.response.status,
          error
        )
      );
    }

    // Handle client errors (4xx) with API message or default
    if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
      const errorData = error.response.data as { message?: string; detail?: string } | undefined;
      const message =
        errorData?.message || errorData?.detail || 'Invalid request. Please check your input.';
      return Promise.reject(
        new ApiRequestError(message, 'CLIENT_ERROR', error.response.status, error)
      );
    }

    // Handle other errors
    if (error.response?.data) {
      const errorData = error.response.data as { message?: string } | undefined;
      const errorMessage = errorData?.message || 'An error occurred';
      return Promise.reject(new Error(errorMessage));
    }

    return Promise.reject(error);
  }
);

// Helper function to create a request with custom timeout
export function createRequest(
  config: AxiosRequestConfig & { operationType?: 'QUICK' | 'STANDARD' | 'LONG_RUNNING' }
): AxiosRequestConfig {
  const { operationType, ...axiosConfig } = config;

  // Set timeout based on operation type if provided
  if (operationType) {
    const timeoutMap = {
      QUICK: 5000,
      STANDARD: 10000,
      LONG_RUNNING: 30000,
    };
    axiosConfig.timeout = timeoutMap[operationType];
  }

  return axiosConfig;
}

// Export configured client
export default apiClient;

// Export types and utilities
export type { AxiosInstance, AxiosRequestConfig };

// API response types
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
