/**
 * Central export for all services
 */

// API services
export { authService } from './api/auth';
export { contextService } from './api/context';
export { default as apiClient } from './api/config';

// WebSocket
export { wsClient, default as WebSocketClient } from './websocket/client';

// Types
export type { ApiResponse, ApiError } from './api/config';
export type { EventHandler, WebSocketConfig } from './websocket/client';
