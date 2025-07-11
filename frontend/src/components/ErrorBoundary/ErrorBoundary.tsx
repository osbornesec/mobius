import { Component, ReactNode } from 'react';
import { captureOwnerStack } from 'react';
import type { 
  ErrorBoundaryProps, 
  ErrorBoundaryState, 
  ErrorInfo 
} from './ErrorBoundary.types';
import { logError } from './errorLogger';
import ErrorFallback from './ErrorFallback';

/**
 * React Error Boundary component for catching and handling errors in child components
 * 
 * @description
 * Implements React's error boundary pattern to catch JavaScript errors anywhere in the
 * child component tree, log those errors, and display a fallback UI instead of the
 * component tree that crashed.
 * 
 * Features:
 * - Automatic error recovery on route changes (configurable)
 * - Custom error logging with dev/prod differentiation
 * - Customizable fallback UI
 * - Error isolation levels (app, page, feature, component)
 * - Reset functionality with custom reset keys
 * 
 * @example
 * ```tsx
 * <ErrorBoundary
 *   fallback={<CustomErrorFallback />}
 *   onError={(error, errorInfo) => console.error(error)}
 *   resetOnRouteChange
 * >
 *   <App />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;
  private previousResetKeys: Array<string | number> = [];

  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
    
    this.previousResetKeys = props.resetKeys || [];
  }

  /**
   * Update state so the next render will show the fallback UI
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error details and component stack
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    const { onError, isolationLevel = 'component' } = this.props;
    
    // Capture owner stack in development for better debugging
    let ownerStack: string | undefined;
    if (import.meta.env.DEV && typeof captureOwnerStack === 'function') {
      try {
        ownerStack = captureOwnerStack();
      } catch {
        // captureOwnerStack might not be available in all React versions
      }
    }
    
    // Update state with error info
    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));
    
    // Log error with enhanced info
    logError(error, errorInfo, {
      metadata: {
        isolationLevel,
        errorCount: this.state.errorCount + 1,
        ownerStack,
      },
    });
    
    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }
  }

  /**
   * Check if component should reset based on prop changes
   */
  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    const { resetKeys = [], resetOnRouteChange = true } = this.props;
    const { hasError } = this.state;
    
    if (hasError) {
      // Check if resetKeys have changed
      const hasResetKeyChanged = resetKeys.some((key, index) => 
        key !== this.previousResetKeys[index]
      );
      
      if (hasResetKeyChanged) {
        this.resetErrorBoundary();
        this.previousResetKeys = [...resetKeys];
      }
      
      // Reset on route change is handled by useErrorReset hook
      // but we keep this for backward compatibility
      if (resetOnRouteChange && window.location.pathname !== prevProps.children?.toString()) {
        this.scheduleReset();
      }
    }
  }

  /**
   * Clean up timeout on unmount
   */
  componentWillUnmount(): void {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  /**
   * Reset error boundary state
   */
  resetErrorBoundary = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * Schedule a reset after a short delay
   */
  private scheduleReset = (): void => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
    
    this.resetTimeoutId = window.setTimeout(() => {
      this.resetErrorBoundary();
    }, 100);
  };

  render(): ReactNode {
    const { 
      children, 
      fallback, 
      showDetails = true,
      isolationLevel = 'component' 
    } = this.props;
    const { hasError, error, errorInfo } = this.state;

    if (hasError && error && errorInfo) {
      // Custom fallback render function
      if (typeof fallback === 'function') {
        return fallback(error, errorInfo, this.resetErrorBoundary);
      }
      
      // Custom fallback component
      if (fallback) {
        return fallback;
      }
      
      // Default fallback
      return (
        <ErrorFallback
          error={error}
          errorInfo={errorInfo}
          reset={this.resetErrorBoundary}
          showDetails={showDetails}
          isolationLevel={isolationLevel}
        />
      );
    }

    return children;
  }
}

export default ErrorBoundary;