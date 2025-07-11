/**
 * API Timeout Configuration
 * Centralized timeout constants for different operation types
 */

// Environment variable fallbacks
const DEFAULT_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT_DEFAULT || '10000');
const LONG_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT_LONG || '30000');
const SHORT_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT_SHORT || '5000');
const MAX_RETRIES = parseInt(import.meta.env.VITE_API_MAX_RETRIES || '3');
const RETRY_DELAY = parseInt(import.meta.env.VITE_API_RETRY_DELAY || '1000');

// Operation type enum
export enum OperationType {
  QUICK = 'QUICK',
  STANDARD = 'STANDARD',
  LONG_RUNNING = 'LONG_RUNNING',
}

// Timeout configuration by operation type
export const TIMEOUT_CONFIG = {
  [OperationType.QUICK]: {
    timeout: SHORT_TIMEOUT,
    description: 'Quick operations: auth checks, simple GETs, health checks',
  },
  [OperationType.STANDARD]: {
    timeout: DEFAULT_TIMEOUT,
    description: 'Standard operations: CRUD operations, searches',
  },
  [OperationType.LONG_RUNNING]: {
    timeout: LONG_TIMEOUT,
    description: 'Long operations: file uploads, data processing, exports',
  },
} as const;

// Specific endpoint timeout overrides
export const ENDPOINT_TIMEOUTS: Record<string, number> = {
  // Auth endpoints - quick
  '/auth/login': SHORT_TIMEOUT,
  '/auth/logout': SHORT_TIMEOUT,
  '/auth/verify': SHORT_TIMEOUT,
  '/auth/refresh': SHORT_TIMEOUT,
  
  // Context operations - vary by type
  '/contexts/import': LONG_TIMEOUT,
  '/contexts/export': LONG_TIMEOUT,
  '/contexts/process': LONG_TIMEOUT,
  '/contexts/analyze': LONG_TIMEOUT,
  
  // File operations - long
  '/files/upload': LONG_TIMEOUT,
  '/files/download': LONG_TIMEOUT,
  
  // Search operations - standard with possibility to extend
  '/search': DEFAULT_TIMEOUT,
  '/contexts/search': DEFAULT_TIMEOUT,
};

// Retry configuration
export const RETRY_CONFIG = {
  maxRetries: MAX_RETRIES,
  initialDelay: RETRY_DELAY,
  maxDelay: 10000, // 10 seconds max delay
  retryableErrors: ['ECONNABORTED', 'ETIMEDOUT', 'ENOTFOUND', 'ENETUNREACH'],
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
};

// Helper to get timeout for a specific endpoint
export function getTimeoutForEndpoint(url: string, method: string = 'GET'): number {
  // Check for specific endpoint overrides
  for (const [endpoint, timeout] of Object.entries(ENDPOINT_TIMEOUTS)) {
    if (url.includes(endpoint)) {
      return timeout;
    }
  }
  
  // Default by method type
  if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
    return DEFAULT_TIMEOUT;
  }
  
  return SHORT_TIMEOUT;
}

// Calculate exponential backoff delay
export function calculateBackoffDelay(attempt: number): number {
  const delay = Math.min(
    RETRY_CONFIG.initialDelay * Math.pow(2, attempt),
    RETRY_CONFIG.maxDelay
  );
  // Add jitter to prevent thundering herd
  return delay + Math.random() * 1000;
}