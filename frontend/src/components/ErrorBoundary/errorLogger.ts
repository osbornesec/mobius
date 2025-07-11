import type { ErrorInfo, SerializedError, ErrorLogConfig } from './ErrorBoundary.types';

/**
 * Default error logging configuration
 */
const defaultConfig: ErrorLogConfig = {
  logToConsole: import.meta.env.DEV,
  sendToService: import.meta.env.PROD,
  serviceEndpoint: import.meta.env.VITE_ERROR_SERVICE_ENDPOINT,
};

/**
 * Serializes an error object for logging
 */
function serializeError(
  error: Error,
  errorInfo: ErrorInfo,
  metadata?: Record<string, unknown>
): SerializedError {
  return {
    message: error.message,
    stack: error.stack,
    name: error.name,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
    componentStack: errorInfo.componentStack,
    metadata,
  };
}

/**
 * Logs error to console in development
 */
function logToConsole(error: Error, errorInfo: ErrorInfo): void {
  console.group('%c🚨 React Error Boundary Caught an Error', 'color: #ff0000; font-weight: bold;');
  console.error('Error:', error);
  console.error('Error Info:', errorInfo);
  console.error('Component Stack:', errorInfo.componentStack);
  
  if (errorInfo.digest) {
    console.error('Error Digest:', errorInfo.digest);
  }
  
  console.groupEnd();
}

/**
 * Sends error to external service in production
 */
async function sendToService(
  serializedError: SerializedError,
  config: ErrorLogConfig
): Promise<void> {
  if (!config.serviceEndpoint) {
    console.warn('Error service endpoint not configured');
    return;
  }

  try {
    const response = await fetch(config.serviceEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(serializedError),
    });

    if (!response.ok) {
      console.error('Failed to send error to service:', response.statusText);
    }
  } catch (err) {
    console.error('Error sending to logging service:', err);
  }
}

/**
 * Main error logging function
 */
export async function logError(
  error: Error,
  errorInfo: ErrorInfo,
  config: Partial<ErrorLogConfig> = {}
): Promise<void> {
  const finalConfig = { ...defaultConfig, ...config };
  
  // Always serialize the error
  const serializedError = serializeError(error, errorInfo, finalConfig.metadata);
  
  // Log to console in development
  if (finalConfig.logToConsole) {
    logToConsole(error, errorInfo);
  }
  
  // Send to service in production
  if (finalConfig.sendToService) {
    await sendToService(serializedError, finalConfig);
  }
  
  // Store in session storage for debugging
  try {
    const errors = JSON.parse(sessionStorage.getItem('mobius_errors') || '[]');
    errors.push(serializedError);
    
    // Keep only the last 10 errors
    if (errors.length > 10) {
      errors.shift();
    }
    
    sessionStorage.setItem('mobius_errors', JSON.stringify(errors));
  } catch (err) {
    console.error('Failed to store error in session storage:', err);
  }
}

/**
 * Retrieves stored errors from session storage
 */
export function getStoredErrors(): SerializedError[] {
  try {
    return JSON.parse(sessionStorage.getItem('mobius_errors') || '[]');
  } catch {
    return [];
  }
}

/**
 * Clears stored errors from session storage
 */
export function clearStoredErrors(): void {
  sessionStorage.removeItem('mobius_errors');
}