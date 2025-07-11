/**
 * Examples demonstrating advanced API timeout and cancellation patterns
 */

import apiClient, { createAbortController, createRequest } from './config';
import { OperationType } from './timeouts';

/**
 * Example 1: Using AbortController for cancellable requests
 * Returns an object with the request promise and abort controller
 *
 * Usage:
 * ```typescript
 * const { promise, controller } = searchWithCancellation('query');
 *
 * // Cancel the request
 * controller.abort();
 *
 * // Handle the promise
 * try {
 *   const result = await promise;
 *   console.log(result);
 * } catch (error) {
 *   if (error.name === 'AbortError') {
 *     console.log('Request was cancelled');
 *   }
 * }
 * ```
 */
export function searchWithCancellation(query: string) {
  const controller = createAbortController();

  const promise = apiClient
    .get('/search', {
      params: { q: query },
      signal: controller.signal,
      timeout: 10000, // 10 second timeout
    })
    .then((response) => response.data)
    .catch((error) => {
      if (error.name === 'AbortError') {
        console.log('Search request was cancelled');
      }
      throw error;
    });

  return {
    promise,
    controller,
    cancel: () => controller.abort(), // Convenience method
  };
}

/**
 * Example 2: Custom timeout for specific operation
 */
export async function processLargeDataset(datasetId: string) {
  const response = await apiClient.post(
    `/datasets/${datasetId}/process`,
    {},
    {
      timeout: 60000, // 60 seconds for large dataset processing
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        console.log(`Processing: ${percentCompleted}%`);
      },
    }
  );

  return response.data;
}

/**
 * Example 3: Using operation type helper
 */
export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post(
    '/files/upload',
    formData,
    createRequest({
      operationType: 'LONG_RUNNING',
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        console.log(`Upload progress: ${percentCompleted}%`);
      },
    })
  );

  return response.data;
}

/**
 * Example 4: Combining timeout with cancellation
 */
export function createCancellableRequest() {
  const controller = createAbortController();

  const makeRequest = async (url: string, options = {}) => {
    return apiClient.get(url, {
      ...options,
      signal: controller.signal,
    });
  };

  return {
    request: makeRequest,
    cancel: () => controller.abort(),
  };
}

/**
 * Example 5: Race condition handling with timeout
 */
export async function fetchWithTimeout<T>(url: string, timeoutMs = 5000): Promise<T> {
  const controller = createAbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await apiClient.get<T>(url, {
      signal: controller.signal,
    });
    return response.data;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Example 6: Batch requests with individual timeouts
 */
export async function batchRequestsWithTimeouts(
  requests: Array<{
    url: string;
    method?: 'GET' | 'POST';
    data?: any;
    timeout?: number;
  }>
) {
  const promises = requests.map((req) =>
    apiClient({
      url: req.url,
      method: req.method || 'GET',
      data: req.data,
      timeout: req.timeout || 10000,
    }).catch((error) => ({
      url: req.url,
      error: error.message,
    }))
  );

  return Promise.allSettled(promises);
}

/**
 * Example 7: Advanced cancellable request manager
 * Manages multiple cancellable requests with cleanup
 *
 * Usage:
 * ```typescript
 * const manager = createCancellableRequestManager();
 *
 * // Start multiple requests
 * const searchPromise = manager.add('search', searchWithCancellation('query').promise);
 * const dataPromise = manager.add('data', apiClient.get('/data'));
 *
 * // Cancel specific request
 * manager.cancel('search');
 *
 * // Cancel all requests
 * manager.cancelAll();
 *
 * // Clean up when done
 * manager.cleanup();
 * ```
 */
export function createCancellableRequestManager() {
  const requests = new Map<string, AbortController>();

  return {
    add<T>(
      key: string,
      requestOrPromise: Promise<T> | { promise: Promise<T>; controller: AbortController }
    ): Promise<T> {
      // If it's already a cancellable request object
      if ('promise' in requestOrPromise && 'controller' in requestOrPromise) {
        requests.set(key, requestOrPromise.controller);
        return requestOrPromise.promise;
      }

      // For regular promises, create a new controller
      const controller = createAbortController();
      requests.set(key, controller);

      // Note: This won't actually cancel the promise, but tracks it
      return requestOrPromise;
    },

    cancel(key: string): boolean {
      const controller = requests.get(key);
      if (controller) {
        controller.abort();
        requests.delete(key);
        return true;
      }
      return false;
    },

    cancelAll(): void {
      requests.forEach((controller) => controller.abort());
      requests.clear();
    },

    cleanup(): void {
      requests.clear();
    },

    getActiveRequests(): string[] {
      return Array.from(requests.keys());
    },
  };
}
