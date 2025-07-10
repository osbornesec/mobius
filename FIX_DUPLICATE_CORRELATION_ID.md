# Fix for Duplicate Correlation ID Logic

## Issue
The code review identified duplicate correlation ID logic between `LoggingMiddleware` and `CorrelationIdMiddleware`. Both middlewares were independently generating and extracting correlation IDs, which could lead to:
- Different correlation IDs for the same request
- Missing `request.state.correlation_id` needed by error handlers
- Redundant code and maintenance burden

## Solution Implemented

### 1. Updated LoggingMiddleware to defer to CorrelationIdMiddleware
Modified `/home/michael_allthingsai_life/devel/mobius/app/middleware/logging.py`:
- Changed to check for `request.state.correlation_id` first (set by CorrelationIdMiddleware)
- Only generates a new correlation ID as a defensive fallback
- Stores the correlation ID in request state if not already present

### 2. Added both middlewares to the application in correct order
Modified `/home/michael_allthingsai_life/devel/mobius/app/main.py`:
- Added CorrelationIdMiddleware first (to set correlation ID)
- Added LoggingMiddleware second (to consume correlation ID)
- Used shared LogConfig for consistency

### 3. Updated tests to use both middlewares
Modified `/home/michael_allthingsai_life/devel/mobius/tests/backend/unit/test_logging.py`:
- Updated all test fixtures to add both middlewares in correct order
- Ensures tests reflect the actual production setup

## Benefits
- Single source of truth for correlation IDs (CorrelationIdMiddleware)
- Consistent correlation IDs throughout request lifecycle
- Proper integration with error handlers via `request.state.correlation_id`
- Clear separation of concerns between middlewares
- Maintainable code with no duplication

## Middleware Order (Important!)
The correct middleware order in FastAPI (added last to first):
1. CorrelationIdMiddleware - Must run first to set correlation ID
2. LoggingMiddleware - Consumes the correlation ID
3. Other middlewares (CORS, Gzip, etc.)

This ensures correlation IDs are available to all subsequent middlewares and handlers.