/**
 * Centralized token storage instance for the application
 * This provides a single source of truth for token management
 */

import { Storage } from '@/utils/storage';

// Token storage interface (duplicated to avoid circular dependency)
export interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;
}

// Default token storage implementation
export class DefaultTokenStorage implements TokenStorage {
  private storage: Storage;
  private readonly ACCESS_TOKEN_KEY = 'accessToken';
  private readonly REFRESH_TOKEN_KEY = 'refreshToken';

  constructor(storage: Storage) {
    this.storage = storage;
  }

  getAccessToken(): string | null {
    return this.storage.get<string>(this.ACCESS_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return this.storage.get<string>(this.REFRESH_TOKEN_KEY);
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.storage.set(this.ACCESS_TOKEN_KEY, accessToken);
    this.storage.set(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  clearTokens(): void {
    this.storage.remove(this.ACCESS_TOKEN_KEY);
    this.storage.remove(this.REFRESH_TOKEN_KEY);
  }
}

// Create a singleton instance of token storage
// This ensures all parts of the application use the same storage instance
export const tokenStorage: TokenStorage = new DefaultTokenStorage(
  new Storage('localStorage', { prefix: 'mobius_auth' })
);

// Export convenience methods for direct access
export const getAccessToken = () => tokenStorage.getAccessToken();
export const getRefreshToken = () => tokenStorage.getRefreshToken();
export const setTokens = (accessToken: string, refreshToken: string) =>
  tokenStorage.setTokens(accessToken, refreshToken);
export const clearTokens = () => tokenStorage.clearTokens();
