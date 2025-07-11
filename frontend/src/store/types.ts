/**
 * Store types for the Mobius frontend application
 */

// Auth Store Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
}

export type AuthStore = AuthState & AuthActions;

// Context Store Types
export interface Context {
  id: string;
  name: string;
  description?: string;
  projectId: string;
  version: string;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface ContextState {
  contexts: Context[];
  activeContext: Context | null;
  isLoading: boolean;
  error: string | null;
}

export interface ContextActions {
  fetchContexts: (projectId: string) => Promise<void>;
  createContext: (context: Omit<Context, 'id' | 'createdAt' | 'updatedAt'>) => Promise<Context>;
  updateContext: (id: string, updates: Partial<Context>) => Promise<void>;
  deleteContext: (id: string) => Promise<void>;
  setActiveContext: (context: Context | null) => void;
  clearError: () => void;
}

export type ContextStore = ContextState & ContextActions;

// UI Store Types
export interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  commandPaletteOpen: boolean;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  createdAt: number;
}

export interface UIActions {
  setTheme: (theme: UIState['theme']) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'createdAt'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export type UIStore = UIState & UIActions;

// WebSocket Store Types
export interface WebSocketState {
  isConnected: boolean;
  reconnectAttempts: number;
  error: string | null;
}

export interface WebSocketActions {
  connect: () => void;
  disconnect: () => void;
  send: (event: string, data: any) => void;
  on: (event: string, handler: (data: any) => void) => void;
  off: (event: string, handler: (data: any) => void) => void;
}

export type WebSocketStore = WebSocketState & WebSocketActions;
