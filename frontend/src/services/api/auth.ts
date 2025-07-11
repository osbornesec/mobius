import apiClient, { ApiResponse, createRequest } from './config';
import { User } from '@/store/types';
import { Storage } from '@/utils/storage';
import { tokenStorage as sharedTokenStorage } from '@/services/tokenStorage';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface RefreshTokenResponse {
  user: User;
  token: string;
}

// Token storage interface for abstraction
export interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;
}

// Default token storage implementation using the Storage abstraction
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

// Auth service configuration options
export interface AuthServiceConfig {
  tokenStorage?: TokenStorage;
}

class AuthService {
  private tokenStorage: TokenStorage;

  constructor(config?: AuthServiceConfig) {
    // Use provided token storage or create default one
    this.tokenStorage =
      config?.tokenStorage ||
      new DefaultTokenStorage(new Storage('localStorage', { prefix: 'mobius_auth' }));
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>(
      '/auth/login',
      {
        email,
        password,
      },
      createRequest({
        operationType: 'QUICK', // Auth should be fast
      })
    );

    // Store tokens using the abstraction
    const { token, refreshToken } = response.data.data;
    this.tokenStorage.setTokens(token, refreshToken);

    return response.data.data;
  }

  async register(data: RegisterRequest): Promise<LoginResponse> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>('/auth/register', data);

    // Store tokens using the abstraction
    const { token, refreshToken } = response.data.data;
    this.tokenStorage.setTokens(token, refreshToken);

    return response.data.data;
  }

  async logout(): Promise<void> {
    await apiClient.post(
      '/auth/logout',
      {},
      createRequest({
        operationType: 'QUICK', // Logout should be fast
      })
    );

    // Clear tokens using the abstraction
    this.tokenStorage.clearTokens();
  }

  /**
   * Refresh the access token using a refresh token
   * @param refreshToken - Optional refresh token. If not provided, will attempt to get from storage
   * @returns RefreshTokenResponse with new access token and user data
   * @throws Error if no refresh token is available
   */
  async refreshToken(refreshToken?: string): Promise<RefreshTokenResponse> {
    // Use provided token or get from storage
    const tokenToUse = refreshToken || this.tokenStorage.getRefreshToken();

    if (!tokenToUse) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post<ApiResponse<RefreshTokenResponse>>(
      '/auth/refresh',
      {
        refreshToken: tokenToUse,
      },
      createRequest({
        operationType: 'QUICK', // Token refresh should be fast
      })
    );

    // Update stored access token
    const { token } = response.data.data;
    const currentRefreshToken = this.tokenStorage.getRefreshToken();
    if (currentRefreshToken) {
      this.tokenStorage.setTokens(token, currentRefreshToken);
    }

    return response.data.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>(
      '/auth/me',
      createRequest({
        operationType: 'QUICK', // Getting current user should be fast
      })
    );
    return response.data.data;
  }

  async updateProfile(updates: Partial<User>): Promise<User> {
    const response = await apiClient.patch<ApiResponse<User>>('/auth/profile', updates);
    return response.data.data;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/change-password', {
      currentPassword,
      newPassword,
    });
  }

  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/auth/forgot-password', { email });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/reset-password', {
      token,
      newPassword,
    });
  }

  // Utility methods for direct token access (useful for testing and special cases)
  getTokenStorage(): TokenStorage {
    return this.tokenStorage;
  }
}

// Default instance with shared token storage
export const authService = new AuthService({
  tokenStorage: sharedTokenStorage,
});

// Export the class for custom instances (useful for testing)
export { AuthService };
