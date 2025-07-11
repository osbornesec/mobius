import type { ErrorInfo, SerializedError, ErrorLogConfig } from './ErrorBoundary.types';
import { sessionStorage, StorageError, StorageErrorType } from '@/utils/storage';

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

  // Store in session storage for debugging with detailed error handling
  try {
    const errors = sessionStorage.get<SerializedError[]>('errors', []) || [];
    errors.push(serializedError);

    // Keep only the last 10 errors
    if (errors.length > 10) {
      errors.shift();
    }

    try {
      sessionStorage.set('errors', errors);
      console.debug('[ErrorLogger] Successfully stored error in session storage', {
        errorCount: errors.length,
        latestError: serializedError.message,
      });
    } catch (storageErr) {
      if (storageErr instanceof StorageError) {
        switch (storageErr.type) {
          case StorageErrorType.QUOTA_EXCEEDED:
            console.warn(
              '[ErrorLogger] Session storage quota exceeded. Attempting to clear old errors.'
            );
            // Try to clear old errors and retry
            try {
              const reducedErrors = errors.slice(-5); // Keep only last 5
              sessionStorage.set('errors', reducedErrors);
              console.info('[ErrorLogger] Successfully stored reduced error set');
            } catch (retryErr) {
              console.error(
                '[ErrorLogger] Failed to store errors even after reducing size:',
                retryErr
              );
            }
            break;

          case StorageErrorType.STORAGE_DISABLED:
            console.warn(
              '[ErrorLogger] Session storage is disabled. Errors will not be persisted.'
            );
            break;

          case StorageErrorType.SERIALIZE_ERROR:
            console.error('[ErrorLogger] Failed to serialize error object:', storageErr);
            // Try storing a simplified version
            try {
              const simplifiedError = {
                message: serializedError.message,
                timestamp: serializedError.timestamp,
                url: serializedError.url,
              };
              const simplifiedErrors = [...errors.slice(0, -1), simplifiedError];
              sessionStorage.set('errors', simplifiedErrors);
              console.info('[ErrorLogger] Stored simplified error instead');
            } catch (simplifiedErr) {
              console.error('[ErrorLogger] Failed to store even simplified error:', simplifiedErr);
            }
            break;

          default:
            console.error('[ErrorLogger] Unexpected storage error:', storageErr);
        }
      } else {
        console.error('[ErrorLogger] Unknown error storing to session storage:', storageErr);
      }
    }
  } catch (err) {
    console.error('[ErrorLogger] Failed to process errors for storage:', err);
  }
}

/**
 * Retrieves stored errors from session storage with detailed error handling
 */
export function getStoredErrors(): SerializedError[] {
  try {
    const errors = sessionStorage.get<SerializedError[]>('errors', []);

    if (!errors || !Array.isArray(errors)) {
      console.warn('[ErrorLogger] Invalid or missing errors in storage, returning empty array');
      return [];
    }

    console.debug('[ErrorLogger] Retrieved stored errors', {
      errorCount: errors.length,
      storageInfo: sessionStorage.getStorageInfo(),
    });

    return errors;
  } catch (error) {
    if (error instanceof StorageError) {
      switch (error.type) {
        case StorageErrorType.STORAGE_DISABLED:
          console.info('[ErrorLogger] Storage is disabled, cannot retrieve errors');
          break;
        case StorageErrorType.PARSE_ERROR:
          console.error('[ErrorLogger] Failed to parse stored errors, data may be corrupted');
          // Attempt to clear corrupted data
          try {
            sessionStorage.remove('errors');
            console.info('[ErrorLogger] Cleared corrupted error data');
          } catch (clearErr) {
            console.error('[ErrorLogger] Failed to clear corrupted data:', clearErr);
          }
          break;
        default:
          console.error('[ErrorLogger] Unexpected error retrieving stored errors:', error);
      }
    } else {
      console.error('[ErrorLogger] Unknown error retrieving stored errors:', error);
    }
    return [];
  }
}

/**
 * Clears stored errors from session storage with logging
 */
export function clearStoredErrors(): void {
  try {
    sessionStorage.remove('errors');
    console.info('[ErrorLogger] Successfully cleared stored errors');
  } catch (error) {
    if (error instanceof StorageError) {
      console.error('[ErrorLogger] Failed to clear stored errors:', {
        errorType: error.type,
        message: error.message,
      });
    } else {
      console.error('[ErrorLogger] Unknown error clearing stored errors:', error);
    }
  }
}
