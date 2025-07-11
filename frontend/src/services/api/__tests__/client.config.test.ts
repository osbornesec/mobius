import { describe, it, expect, beforeEach, vi, MockedFunction } from 'vitest';
import axios from 'axios';
import { createMockAxiosInstance } from './testHelpers';

// Mock axios
vi.mock('axios');

describe('API Client Configuration', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Create mock axios instance
    const { mockInstance } = createMockAxiosInstance();
    
    // Mock axios.create to return our mock instance
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockInstance as any);

    // Re-import to get fresh instance with mocks
    vi.resetModules();
  });

  it('should be configured with correct base URL and timeout', async () => {
    // Import to trigger axios.create
    await import('../config');

    expect(axios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  });

  it('should set up request interceptor', async () => {
    const { mockInstance } = createMockAxiosInstance();
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockInstance as any);

    await import('../config');

    expect(mockInstance.interceptors.request.use).toHaveBeenCalledTimes(1);
    expect(mockInstance.interceptors.request.use).toHaveBeenCalledWith(
      expect.any(Function),
      expect.any(Function)
    );
  });

  it('should set up response interceptor', async () => {
    const { mockInstance } = createMockAxiosInstance();
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockInstance as any);

    await import('../config');

    expect(mockInstance.interceptors.response.use).toHaveBeenCalledTimes(1);
    expect(mockInstance.interceptors.response.use).toHaveBeenCalledWith(
      expect.any(Function),
      expect.any(Function)
    );
  });

  it('should export the configured axios instance as default', async () => {
    const { mockInstance } = createMockAxiosInstance();
    (axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockInstance as any);

    const { default: apiClient } = await import('../config');

    expect(apiClient).toBeDefined();
    expect(typeof apiClient).toBe('object');
  });

  it('should export ApiRequestError class', async () => {
    const { ApiRequestError } = await import('../config');

    expect(ApiRequestError).toBeDefined();
    expect(typeof ApiRequestError).toBe('function');
  });
});