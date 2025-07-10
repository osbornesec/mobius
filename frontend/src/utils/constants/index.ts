/**
 * Application constants
 */

// API Routes
export const API_ROUTES = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    PROFILE: '/auth/profile',
    CHANGE_PASSWORD: '/auth/change-password',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
  },
  CONTEXTS: {
    LIST: '/contexts',
    DETAIL: (id: string) => `/contexts/${id}`,
    CREATE: '/contexts',
    UPDATE: (id: string) => `/contexts/${id}`,
    DELETE: (id: string) => `/contexts/${id}`,
    SEARCH: '/contexts/search',
    DUPLICATE: (id: string) => `/contexts/${id}/duplicate`,
    EXPORT: (id: string) => `/contexts/${id}/export`,
    IMPORT: '/contexts/import',
  },
  PROJECTS: {
    LIST: '/projects',
    DETAIL: (id: string) => `/projects/${id}`,
    CREATE: '/projects',
    UPDATE: (id: string) => `/projects/${id}`,
    DELETE: (id: string) => `/projects/${id}`,
  },
} as const;

// Application Routes
export const APP_ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  DASHBOARD: '/dashboard',
  PROJECTS: '/projects',
  PROJECT_DETAIL: (id: string) => `/projects/${id}`,
  CONTEXTS: '/contexts',
  CONTEXT_DETAIL: (id: string) => `/contexts/${id}`,
  SETTINGS: '/settings',
  PROFILE: '/profile',
} as const;

// WebSocket Events
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  CONTEXT: {
    CREATED: 'context:created',
    UPDATED: 'context:updated',
    DELETED: 'context:deleted',
  },
  PROJECT: {
    CREATED: 'project:created',
    UPDATED: 'project:updated',
    DELETED: 'project:deleted',
  },
  NOTIFICATION: 'notification',
} as const;

// Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken',
  REFRESH_TOKEN: 'refreshToken',
  THEME: 'theme',
  SIDEBAR_STATE: 'sidebarState',
} as const;

// Query Keys for React Query
export const QUERY_KEYS = {
  AUTH: {
    USER: ['auth', 'user'],
  },
  CONTEXTS: {
    LIST: (projectId?: string) => ['contexts', { projectId }],
    DETAIL: (id: string) => ['contexts', id],
    SEARCH: (params: any) => ['contexts', 'search', params],
  },
  PROJECTS: {
    LIST: ['projects'],
    DETAIL: (id: string) => ['projects', id],
  },
} as const;

// UI Constants
export const UI_CONSTANTS = {
  NOTIFICATION_DURATION: 5000, // 5 seconds
  DEBOUNCE_DELAY: 300, // 300ms
  PAGE_SIZE: 20,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  SUPPORTED_FILE_TYPES: ['.json', '.yaml', '.yml'],
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  GENERIC: 'An unexpected error occurred. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  VALIDATION: 'Please check your input and try again.',
  FILE_TOO_LARGE: `File size must be less than ${UI_CONSTANTS.MAX_FILE_SIZE / 1024 / 1024}MB`,
  UNSUPPORTED_FILE_TYPE: `Supported file types: ${UI_CONSTANTS.SUPPORTED_FILE_TYPES.join(', ')}`,
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Welcome back!',
  LOGOUT: 'Successfully logged out.',
  REGISTER: 'Account created successfully!',
  CONTEXT_CREATED: 'Context created successfully.',
  CONTEXT_UPDATED: 'Context updated successfully.',
  CONTEXT_DELETED: 'Context deleted successfully.',
  PROJECT_CREATED: 'Project created successfully.',
  PROJECT_UPDATED: 'Project updated successfully.',
  PROJECT_DELETED: 'Project deleted successfully.',
  PROFILE_UPDATED: 'Profile updated successfully.',
  PASSWORD_CHANGED: 'Password changed successfully.',
} as const;