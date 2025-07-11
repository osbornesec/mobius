import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import useAuthStore from '@/store/authStore';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token to requests
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      const timeoutError = new Error(
        'Request timed out. Please check your connection and try again.'
      );
      (timeoutError as any).code = 'TIMEOUT';
      (timeoutError as any).originalError = error;
      return Promise.reject(timeoutError);
    }

    // Handle network errors
    if (!error.response && error.request) {
      const networkError = new Error('Network error. Please check your internet connection.');
      (networkError as any).code = 'NETWORK_ERROR';
      (networkError as any).originalError = error;
      return Promise.reject(networkError);
    }

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        await useAuthStore.getState().refreshToken();

        // Retry original request with new token
        const token = localStorage.getItem('authToken');
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
        }

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle server errors (5xx) with user-friendly message
    if (error.response?.status && error.response.status >= 500) {
      const serverError = new Error(
        'Server error. Our team has been notified. Please try again later.'
      );
      (serverError as any).code = 'SERVER_ERROR';
      (serverError as any).status = error.response.status;
      (serverError as any).originalError = error;
      return Promise.reject(serverError);
    }

    // Handle client errors (4xx) with API message or default
    if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
      const errorData = error.response.data as any;
      const message =
        errorData?.message || errorData?.detail || 'Invalid request. Please check your input.';
      const clientError = new Error(message);
      (clientError as any).code = 'CLIENT_ERROR';
      (clientError as any).status = error.response.status;
      (clientError as any).originalError = error;
      return Promise.reject(clientError);
    }

    // Handle other errors
    if (error.response?.data) {
      const errorMessage = (error.response.data as any).message || 'An error occurred';
      return Promise.reject(new Error(errorMessage));
    }

    return Promise.reject(error);
  }
);

// Export configured client
export default apiClient;

// Export types and utilities
export type { AxiosInstance, AxiosRequestConfig };

// API response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}
