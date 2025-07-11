/**
 * Examples demonstrating advanced API timeout and cancellation patterns
 */

import apiClient, { createAbortController, createRequest } from './config';
import { OperationType } from './timeouts';

/**
 * Example 1: Using AbortController for cancellable requests
 */
export async function searchWithCancellation(query: string) {
  const controller = createAbortController();
  
  try {
    const response = await apiClient.get('/search', {
      params: { q: query },
      signal: controller.signal,
      timeout: 10000, // 10 second timeout
    });
    
    return response.data;
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Search request was cancelled');
    }
    throw error;
  }
  
  // To cancel: controller.abort()
  return { controller };
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
export async function fetchWithTimeout<T>(
  url: string,
  timeoutMs: number = 5000
): Promise<T> {
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
export async function batchRequestsWithTimeouts(requests: Array<{
  url: string;
  method?: 'GET' | 'POST';
  data?: any;
  timeout?: number;
}>) {
  const promises = requests.map(req =>
    apiClient({
      url: req.url,
      method: req.method || 'GET',
      data: req.data,
      timeout: req.timeout || 10000,
    }).catch(error => ({
      url: req.url,
      error: error.message,
    }))
  );
  
  return Promise.allSettled(promises);
}