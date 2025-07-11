import { useState } from 'react';
import type { ErrorFallbackProps } from './ErrorBoundary.types';

/**
 * Default error fallback component for the ErrorBoundary
 *
 * @description
 * Provides a user-friendly error display with different UI based on the isolation level
 * and environment (development vs production). Includes error details in development
 * and a reset button to recover from the error state.
 */
function ErrorFallback({
  error,
  errorInfo,
  reset,
  showDetails,
  isolationLevel,
}: ErrorFallbackProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isDev = import.meta.env.DEV;

  // Determine severity and styling based on isolation level
  const getSeverityStyles = () => {
    switch (isolationLevel) {
      case 'app':
        return {
          container: 'min-h-screen flex items-center justify-center bg-red-50',
          card: 'max-w-2xl w-full bg-white shadow-2xl rounded-lg p-8',
          icon: '🚨',
          title: 'Application Error',
          description: 'We apologize, but something went wrong with the application.',
        };
      case 'page':
        return {
          container: 'min-h-[60vh] flex items-center justify-center',
          card: 'max-w-xl w-full bg-red-50 border border-red-200 rounded-lg p-6',
          icon: '⚠️',
          title: 'Page Error',
          description: 'This page encountered an error and cannot be displayed.',
        };
      case 'feature':
        return {
          container: 'p-4',
          card: 'bg-orange-50 border border-orange-200 rounded-lg p-4',
          icon: '⚡',
          title: 'Feature Unavailable',
          description: 'This feature is temporarily unavailable.',
        };
      case 'component':
      default:
        return {
          container: 'p-2',
          card: 'bg-yellow-50 border border-yellow-200 rounded p-3',
          icon: '⚠️',
          title: 'Component Error',
          description: 'This component cannot be displayed.',
        };
    }
  };

  const styles = getSeverityStyles();

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {/* Error Header */}
        <div className="flex items-start space-x-3">
          <span className="text-2xl" role="img" aria-label="Error">
            {styles.icon}
          </span>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900">{styles.title}</h2>
            <p className="mt-1 text-gray-600">{styles.description}</p>
          </div>
        </div>

        {/* Error Details (Dev Mode or when showDetails is true) */}
        {(isDev || showDetails) && (
          <div className="mt-4">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:underline"
            >
              {isExpanded ? 'Hide' : 'Show'} Error Details
            </button>

            {isExpanded && (
              <div className="mt-3 space-y-3">
                {/* Error Message */}
                <div className="bg-gray-100 rounded p-3">
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">Error Message:</h3>
                  <code className="text-xs text-red-600 break-all">{error.message}</code>
                </div>

                {/* Component Stack */}
                {errorInfo.componentStack && (
                  <div className="bg-gray-100 rounded p-3">
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Component Stack:</h3>
                    <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">
                      {errorInfo.componentStack}
                    </pre>
                  </div>
                )}

                {/* Error Stack (Dev Only) */}
                {isDev && error.stack && (
                  <div className="bg-gray-100 rounded p-3">
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Error Stack:</h3>
                    <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">
                      {error.stack}
                    </pre>
                  </div>
                )}

                {/* Error Digest */}
                {errorInfo.digest && (
                  <div className="bg-gray-100 rounded p-3">
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Error ID:</h3>
                    <code className="text-xs text-gray-600">{errorInfo.digest}</code>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex items-center space-x-3">
          <button
            type="button"
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Try Again
          </button>

          {isolationLevel === 'app' && (
            <button
              type="button"
              onClick={() => (window.location.href = '/')}
              className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Go to Home
            </button>
          )}
        </div>

        {/* Support Information */}
        {(isolationLevel === 'app' || isolationLevel === 'page') && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              If this problem persists, please contact support with error ID:
              <code className="ml-1 text-xs bg-gray-100 px-1 py-0.5 rounded">
                {errorInfo.digest || new Date().getTime()}
              </code>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ErrorFallback;
