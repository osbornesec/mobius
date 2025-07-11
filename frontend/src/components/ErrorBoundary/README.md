# Error Boundary Component

A comprehensive React Error Boundary system for the Mobius platform that provides graceful error handling with multiple isolation levels and automatic recovery mechanisms.

## Features

- **Multiple Isolation Levels**: App, Page, Feature, and Component level error boundaries
- **Automatic Recovery**: Reset on route changes (configurable)
- **Custom Error Logging**: Different behaviors for development and production
- **Flexible Fallback UI**: Custom fallback components or render functions
- **Error Persistence**: Stores errors in session storage for debugging
- **TypeScript Support**: Fully typed with no `any` types
- **React 19 Ready**: Uses latest error boundary patterns

## Usage

### Basic Usage

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function MyComponent() {
  return (
    <ErrorBoundary>
      <ComponentThatMightError />
    </ErrorBoundary>
  );
}
```

### App-Level Boundary

```tsx
// In App.tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary
      isolationLevel="app"
      resetOnRouteChange
      onError={(error, errorInfo) => {
        console.error('App Error:', error);
      }}
    >
      <Router>
        {/* Your app routes */}
      </Router>
    </ErrorBoundary>
  );
}
```

### Page-Level Boundary

```tsx
// In a page component
import ErrorBoundary from '@/components/ErrorBoundary';

function DashboardPage() {
  return (
    <ErrorBoundary isolationLevel="page">
      <DashboardContent />
    </ErrorBoundary>
  );
}
```

### Feature-Level Boundary

```tsx
// Around a specific feature
import ErrorBoundary from '@/components/ErrorBoundary';

function ContextBuilder() {
  return (
    <ErrorBoundary
      isolationLevel="feature"
      fallback={<div>Context Builder is temporarily unavailable</div>}
    >
      <ContextBuilderContent />
    </ErrorBoundary>
  );
}
```

### Custom Fallback Function

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function MyComponent() {
  return (
    <ErrorBoundary
      fallback={(error, errorInfo, reset) => (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{error.message}</p>
          <button onClick={reset}>Try Again</button>
        </div>
      )}
    >
      <ComponentContent />
    </ErrorBoundary>
  );
}
```

### With Reset Keys

```tsx
import ErrorBoundary from '@/components/ErrorBoundary';

function DataComponent({ dataId }) {
  return (
    <ErrorBoundary
      resetKeys={[dataId]} // Resets when dataId changes
    >
      <DataDisplay dataId={dataId} />
    </ErrorBoundary>
  );
}
```

## Hooks

### useErrorReset

Automatically resets error boundaries on route changes:

```tsx
import { useErrorReset } from '@/components/ErrorBoundary';

function CustomErrorBoundary({ children }) {
  const [hasError, setHasError] = useState(false);

  useErrorReset(
    () => setHasError(false),
    hasError // Only reset when there's an error
  );

  // Error boundary implementation
}
```

### useManualErrorReset

Provides a manual reset function with optional delay:

```tsx
import { useManualErrorReset } from '@/components/ErrorBoundary';

function ErrorDisplay() {
  const resetError = useManualErrorReset(500); // 500ms delay

  return (
    <button onClick={resetError}>
      Reset Application
    </button>
  );
}
```

## Error Logging

The error logger automatically:
- Logs to console in development
- Sends to external service in production (when configured)
- Stores last 10 errors in session storage

### Accessing Stored Errors

```tsx
import { getStoredErrors, clearStoredErrors } from '@/components/ErrorBoundary';

// Get stored errors
const errors = getStoredErrors();

// Clear stored errors
clearStoredErrors();
```

## Configuration

Set environment variables for production error logging:

```env
VITE_ERROR_SERVICE_ENDPOINT=https://api.example.com/errors
```

## Best Practices

1. **Use Multiple Boundaries**: Don't rely on a single app-level boundary. Use page and feature boundaries for better UX.

2. **Meaningful Fallbacks**: Provide context-appropriate fallback UI based on the isolation level.

3. **Log Strategically**: Use the `onError` prop for custom logging logic specific to different parts of your app.

4. **Test Error Scenarios**: Always test your error boundaries with real error conditions.

5. **Reset Wisely**: Use `resetKeys` for data-dependent components and `resetOnRouteChange` for navigation-based recovery.

## Testing

```tsx
// Test component that throws an error
function ErrorTest() {
  const [shouldError, setShouldError] = useState(false);

  if (shouldError) {
    throw new Error('Test error');
  }

  return (
    <button onClick={() => setShouldError(true)}>
      Trigger Error
    </button>
  );
}

// Wrap in error boundary for testing
<ErrorBoundary>
  <ErrorTest />
</ErrorBoundary>
```
