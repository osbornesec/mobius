import type { User } from '@/types/auth';

// Mock user data
export const MOCK_USER: User = {
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  createdAt: '2024-01-01',
  updatedAt: '2024-01-01',
};

export const MOCK_ADMIN_USER: User = {
  id: '2',
  email: 'admin@example.com',
  name: 'Admin User',
  role: 'admin',
  createdAt: '2024-01-01',
  updatedAt: '2024-01-01',
};

// Mock tokens
export const MOCK_ACCESS_TOKEN = 'mock-access-token-123';
export const MOCK_REFRESH_TOKEN = 'mock-refresh-token-456';
export const MOCK_NEW_ACCESS_TOKEN = 'mock-new-access-token-789';
export const MOCK_NEW_REFRESH_TOKEN = 'mock-new-refresh-token-012';

// Mock auth responses
export const MOCK_LOGIN_RESPONSE = {
  user: MOCK_USER,
  token: MOCK_ACCESS_TOKEN,
  refreshToken: MOCK_REFRESH_TOKEN,
};

export const MOCK_REFRESH_RESPONSE = {
  user: MOCK_USER,
  token: MOCK_NEW_ACCESS_TOKEN,
  refreshToken: MOCK_NEW_REFRESH_TOKEN,
};

// Mock credentials
export const MOCK_CREDENTIALS = {
  email: 'test@example.com',
  password: 'password123',
};

// Mock registration data
export const MOCK_REGISTRATION_DATA = {
  email: 'new@example.com',
  password: 'password123',
  name: 'New User',
};

// Error messages
export const AUTH_ERROR_MESSAGES = {
  INVALID_CREDENTIALS: 'Invalid credentials',
  TOKEN_EXPIRED: 'Token expired',
  NO_REFRESH_TOKEN: 'No refresh token available',
  NETWORK_ERROR: 'Network error',
  LOGIN_FAILED: 'Login failed',
};