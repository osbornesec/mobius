# API Timeout Configuration Guide

## Overview

The Mobius frontend now implements a comprehensive timeout strategy with the following features:

- **Tiered timeout system** based on operation types
- **Automatic retry logic** with exponential backoff
- **Environment-based configuration**
- **Per-endpoint timeout customization**
- **AbortController support** for request cancellation
- **Performance monitoring** and metrics tracking

## Timeout Tiers

### 1. Quick Operations (5 seconds)
- Authentication checks
- Simple GET requests
- Health checks
- User profile fetches

### 2. Standard Operations (10 seconds)
- CRUD operations
- Search queries
- Data fetching
- Form submissions

### 3. Long-Running Operations (30 seconds)
- File uploads/downloads
- Data processing
- Export/import operations
- Batch operations

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
VITE_API_TIMEOUT_DEFAULT=10000        # 10 seconds
VITE_API_TIMEOUT_LONG=30000          # 30 seconds
VITE_API_TIMEOUT_SHORT=5000          # 5 seconds
VITE_API_MAX_RETRIES=3               # Max retry attempts
VITE_API_RETRY_DELAY=1000            # Initial retry delay
```

### Usage Examples

#### 1. Using Operation Types

```typescript
import apiClient, { createRequest } from '@/services/api/config';

// Quick operation
const user = await apiClient.get('/auth/me', createRequest({
  operationType: 'QUICK'
}));

// Long-running operation
const result = await apiClient.post('/data/process', data, createRequest({
  operationType: 'LONG_RUNNING'
}));
```

#### 2. Custom Timeout

```typescript
// Override timeout for specific request
const response = await apiClient.get('/api/endpoint', {
  timeout: 45000  // 45 seconds
});
```

#### 3. Request Cancellation

```typescript
import { createAbortController } from '@/services/api/config';

const controller = createAbortController();

// Make request
const promise = apiClient.get('/api/search', {
  params: { q: query },
  signal: controller.signal
});

// Cancel if needed
controller.abort();
```

#### 4. Progress Tracking

```typescript
const response = await apiClient.post('/files/upload', formData, {
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`Upload: ${percentCompleted}%`);
  }
});
```

## Retry Logic

The system automatically retries failed requests with exponential backoff:

- **Retryable errors**: Network timeouts, 5xx errors, 429 (rate limit)
- **Max retries**: 3 attempts (configurable)
- **Backoff**: 1s, 2s, 4s (with jitter)
- **Non-retryable**: 4xx errors (except 408, 429)

## Performance Monitoring

Track API performance in development:

```typescript
import { apiMonitor } from '@/services/api/monitoring';

// Get endpoint statistics
const stats = apiMonitor.getEndpointStats('/api/contexts');
console.log(stats);
// {
//   totalCalls: 150,
//   avgDuration: 245,
//   p95Duration: 890,
//   timeoutRate: 0.5,
//   errorRate: 1.2
// }

// Get overall summary
const summary = apiMonitor.getPerformanceSummary();
```

## Best Practices

1. **Choose appropriate timeout tiers** based on operation complexity
2. **Implement loading states** for long-running operations
3. **Use AbortController** for user-cancellable operations
4. **Monitor timeout rates** in production
5. **Adjust timeouts** based on real-world performance data
6. **Handle timeout errors** gracefully with user-friendly messages

## Error Handling

The system provides enhanced error messages for different scenarios:

```typescript
try {
  const data = await apiClient.get('/api/data');
} catch (error) {
  if (error.code === 'TIMEOUT') {
    // "Request timed out. The server might be slow or your connection unstable."
  } else if (error.code === 'NETWORK_ERROR') {
    // "Cannot reach the server. Please check your internet connection."
  }
  // Handle error appropriately
}
```

## Migration Guide

To update existing code:

1. Replace hardcoded timeouts with operation types
2. Use `createRequest()` helper for typed configuration
3. Add progress handlers for file operations
4. Implement cancellation for search/filter operations
