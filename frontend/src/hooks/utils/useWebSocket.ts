import { useEffect, useCallback } from 'react';
import { wsClient } from '@/services/websocket/client';
import type { EventHandler } from '@/services/websocket/client';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { autoConnect = true, onConnect, onDisconnect, onError } = options;

  useEffect(() => {
    if (autoConnect) {
      wsClient.connect();
    }

    if (onConnect) {
      wsClient.on('connect', onConnect);
    }
    if (onDisconnect) {
      wsClient.on('disconnect', onDisconnect);
    }
    if (onError) {
      wsClient.on('error', onError);
    }

    return () => {
      if (onConnect) {
        wsClient.off('connect', onConnect);
      }
      if (onDisconnect) {
        wsClient.off('disconnect', onDisconnect);
      }
      if (onError) {
        wsClient.off('error', onError);
      }
    };
  }, [autoConnect, onConnect, onDisconnect, onError]);

  const emit = useCallback((event: string, data?: any) => {
    wsClient.emit(event, data);
  }, []);

  const on = useCallback((event: string, handler: EventHandler) => {
    wsClient.on(event, handler);
    return () => wsClient.off(event, handler);
  }, []);

  const off = useCallback((event: string, handler: EventHandler) => {
    wsClient.off(event, handler);
  }, []);

  const isConnected = useCallback(() => {
    return wsClient.isConnected();
  }, []);

  return {
    emit,
    on,
    off,
    isConnected,
    connect: () => wsClient.connect(),
    disconnect: () => wsClient.disconnect(),
  };
}