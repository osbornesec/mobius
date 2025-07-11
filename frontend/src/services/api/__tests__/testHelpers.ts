import { vi } from 'vitest';
import { AxiosRequestConfig, AxiosResponse } from 'axios';
import { MOCK_ACCESS_TOKEN, MOCK_NEW_ACCESS_TOKEN } from '@/__tests__/mocks/auth';

// Mock localStorage
export const createLocalStorageMock = () => {
  const mock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  };
  return mock as Storage;
};

// Mock window.location
export const createLocationMock = () => ({
  href: '',
});

// Mock axios instance
export const createMockAxiosInstance = () => {
  let requestInterceptor: any;
  let responseInterceptor: any;

  const mockInstance = {
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

  return {
    mockInstance,
    getInterceptors: () => ({ requestInterceptor, responseInterceptor }),
  };
};

// Re-export tokens from centralized mocks for backward compatibility
export const mockAuthToken = MOCK_ACCESS_TOKEN;
export const mockNewAuthToken = MOCK_NEW_ACCESS_TOKEN;

export const createMockResponse = (data: any, status = 200): AxiosResponse => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {} as AxiosRequestConfig,
});

export const createMockConfig = (overrides?: Partial<AxiosRequestConfig>): AxiosRequestConfig => ({
  headers: {},
  url: '/test',
  method: 'GET',
  ...overrides,
});
