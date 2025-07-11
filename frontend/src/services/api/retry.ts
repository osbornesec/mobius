import { AxiosError, AxiosRequestConfig } from 'axios';
import { RETRY_CONFIG, calculateBackoffDelay } from './timeouts';
import { ApiRequestError } from './config';

interface RetryState {
  retryCount: number;
  lastError?: Error;
}

// Retry state map to track retries per request
const retryStateMap = new WeakMap<AxiosRequestConfig, RetryState>();

/**
 * Determines if an error is retryable
 */
export function isRetryableError(error: AxiosError): boolean {
  // Check if it's a network/timeout error
  if (error.code && RETRY_CONFIG.retryableErrors.includes(error.code)) {
    return true;
  }

  // Check if it's a retryable status code
  if (error.response?.status && RETRY_CONFIG.retryableStatusCodes.includes(error.response.status)) {
    return true;
  }

  // Don't retry client errors (4xx) except specific ones
  if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
    return error.response.status === 408 || error.response.status === 429;
  }

  return false;
}

/**
 * Get or initialize retry state for a request
 */
export function getRetryState(config: AxiosRequestConfig): RetryState {
  if (!retryStateMap.has(config)) {
    retryStateMap.set(config, { retryCount: 0 });
  }
  return retryStateMap.get(config)!;
}

/**
 * Clear retry state for a request
 */
export function clearRetryState(config: AxiosRequestConfig): void {
  retryStateMap.delete(config);
}

/**
 * Sleep for a specified duration
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a timeout error
 */
export function createTimeoutError(timeout: number): ApiRequestError {
  return new ApiRequestError(
    `Request timed out after ${timeout}ms. Please try again.`,
    'TIMEOUT',
    408
  );
}

/**
 * Format retry attempt message for logging
 */
export function formatRetryMessage(attempt: number, maxRetries: number, delay: number): string {
  return `Retry attempt ${attempt}/${maxRetries} after ${delay}ms delay`;
}

/**
 * Handle specific error types with appropriate messages
 */
export function enhanceErrorMessage(error: AxiosError): string {
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
    return 'Request timed out. The server might be slow or your connection unstable.';
  }

  if (error.code === 'ENETUNREACH' || error.code === 'ENOTFOUND') {
    return 'Cannot reach the server. Please check your internet connection.';
  }

  if (error.response?.status === 429) {
    const retryAfter = error.response.headers['retry-after'];
    if (retryAfter) {
      return `Too many requests. Please try again in ${retryAfter} seconds.`;
    }
    return 'Too many requests. Please slow down and try again.';
  }

  if (error.response?.status === 503) {
    return 'Service temporarily unavailable. Please try again in a few moments.';
  }

  return 'An unexpected error occurred. Please try again.';
}
