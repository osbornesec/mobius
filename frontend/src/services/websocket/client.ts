import { io, Socket } from 'socket.io-client';

export interface WebSocketConfig {
  url?: string;
  autoConnect?: boolean;
  reconnection?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
}

export type EventHandler = (data: any) => void;

class WebSocketClient {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private config: WebSocketConfig;

  constructor(config: WebSocketConfig = {}) {
    this.config = {
      url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      ...config,
    };
  }

  connect(): void {
    if (this.socket?.connected) {
      return;
    }

    const token = localStorage.getItem('authToken');

    this.socket = io(this.config.url!, {
      auth: { token },
      reconnection: this.config.reconnection,
      reconnectionAttempts: this.config.reconnectionAttempts,
      reconnectionDelay: this.config.reconnectionDelay,
    });

    this.setupEventListeners();
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  emit(event: string, data?: any): void {
    if (!this.socket?.connected) {
      console.warn('WebSocket is not connected');
      return;
    }
    this.socket.emit(event, data);
  }

  on(event: string, handler: EventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);

    // If socket exists, add the listener
    if (this.socket) {
      this.socket.on(event, handler);
    }
  }

  off(event: string, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(event);
      }
    }

    // If socket exists, remove the listener
    if (this.socket) {
      this.socket.off(event, handler);
    }
  }

  once(event: string, handler: EventHandler): void {
    const onceHandler = (data: any) => {
      handler(data);
      this.off(event, onceHandler);
    };
    this.on(event, onceHandler);
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    // Re-attach all existing event handlers
    this.eventHandlers.forEach((handlers, event) => {
      handlers.forEach((handler) => {
        this.socket!.on(event, handler);
      });
    });

    // Built-in events
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts');
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnection error:', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
    });
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();

// Export class for custom instances
export default WebSocketClient;