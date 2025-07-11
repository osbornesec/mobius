import { ReactNode } from 'react';

/**
 * Error information provided by React when an error is caught
 */
export interface ErrorInfo {
  componentStack: string;
  digest?: string;
}

/**
 * Props for the ErrorBoundary component
 */
export interface ErrorBoundaryProps {
  /**
   * Children components to be wrapped by the error boundary
   */
  children: ReactNode;
  
  /**
   * Custom fallback component or render function
   */
  fallback?: ReactNode | ((error: Error, errorInfo: ErrorInfo, reset: () => void) => ReactNode);
  
  /**
   * Whether to show error details in development mode
   * @default true
   */
  showDetails?: boolean;
  
  /**
   * Custom error logging function
   */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  
  /**
   * Whether to reset error state when route changes
   * @default true
   */
  resetOnRouteChange?: boolean;
  
  /**
   * Custom reset keys that trigger error boundary reset when changed
   */
  resetKeys?: Array<string | number>;
  
  /**
   * Isolation level for the error boundary
   * - 'app': Top-level application boundary
   * - 'page': Page-level boundary
   * - 'feature': Feature-specific boundary
   * - 'component': Individual component boundary
   * @default 'component'
   */
  isolationLevel?: 'app' | 'page' | 'feature' | 'component';
}

/**
 * State for the ErrorBoundary component
 */
export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

/**
 * Props for the ErrorFallback component
 */
export interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo;
  reset: () => void;
  showDetails: boolean;
  isolationLevel: 'app' | 'page' | 'feature' | 'component';
}

/**
 * Error logging configuration
 */
export interface ErrorLogConfig {
  /**
   * Whether to log errors to console in development
   * @default true
   */
  logToConsole?: boolean;
  
  /**
   * Whether to send errors to external service in production
   * @default true
   */
  sendToService?: boolean;
  
  /**
   * Additional metadata to include with error logs
   */
  metadata?: Record<string, unknown>;
  
  /**
   * Error service endpoint URL
   */
  serviceEndpoint?: string;
}

/**
 * Serialized error for logging
 */
export interface SerializedError {
  message: string;
  stack?: string;
  name: string;
  timestamp: string;
  userAgent: string;
  url: string;
  componentStack: string;
  metadata?: Record<string, unknown>;
  isolationLevel?: string;
}