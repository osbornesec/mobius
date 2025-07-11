/**
 * Error Boundary module exports
 *
 * @module ErrorBoundary
 */

// Main component
export { default as ErrorBoundary } from './ErrorBoundary';
export { default } from './ErrorBoundary';

// Fallback component
export { default as ErrorFallback } from './ErrorFallback';

// Hooks
export { useErrorReset, useManualErrorReset } from './useErrorReset';

// Error logger utilities
export {
  logError,
  getStoredErrors,
  clearStoredErrors
} from './errorLogger';

// Types
export type {
  ErrorBoundaryProps,
  ErrorBoundaryState,
  ErrorFallbackProps,
  ErrorInfo,
  ErrorLogConfig,
  SerializedError,
} from './ErrorBoundary.types';
