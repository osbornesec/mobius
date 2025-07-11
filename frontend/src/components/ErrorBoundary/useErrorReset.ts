import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Hook that provides automatic error boundary reset on route changes
 * 
 * @description
 * This hook monitors route changes and triggers a reset callback when navigation occurs.
 * Useful for automatically recovering from errors when users navigate away from the
 * problematic route.
 * 
 * @param resetFn - Function to call when route changes
 * @param enabled - Whether to enable automatic reset on route change
 * 
 * @example
 * ```tsx
 * function MyErrorBoundary({ children }) {
 *   const [hasError, setHasError] = useState(false);
 *   
 *   useErrorReset(
 *     () => setHasError(false),
 *     hasError // Only reset when there's an error
 *   );
 *   
 *   // ... rest of error boundary logic
 * }
 * ```
 */
export function useErrorReset(
  resetFn: () => void,
  enabled: boolean = true
): void {
  const location = useLocation();
  const previousLocation = useRef(location.pathname);
  const isFirstRender = useRef(true);

  useEffect(() => {
    // Skip the first render to avoid immediate reset
    if (isFirstRender.current) {
      isFirstRender.current = false;
      previousLocation.current = location.pathname;
      return;
    }

    // Check if route has changed and reset is enabled
    if (enabled && location.pathname !== previousLocation.current) {
      resetFn();
      previousLocation.current = location.pathname;
    }
  }, [location.pathname, resetFn, enabled]);
}

/**
 * Hook that provides a manual error reset function with optional delay
 * 
 * @param delay - Optional delay in milliseconds before reset
 * @returns Function to trigger error reset
 * 
 * @example
 * ```tsx
 * function ErrorComponent() {
 *   const resetError = useManualErrorReset(500); // 500ms delay
 *   
 *   return (
 *     <button onClick={resetError}>
 *       Reset Error
 *     </button>
 *   );
 * }
 * ```
 */
export function useManualErrorReset(delay?: number): () => void {
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    // Cleanup timeout on unmount
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const reset = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (delay) {
      timeoutRef.current = window.setTimeout(() => {
        window.location.reload();
      }, delay);
    } else {
      window.location.reload();
    }
  };

  return reset;
}