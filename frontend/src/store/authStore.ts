import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { AuthStore, User } from './types';
import { authService } from '@/services/api/auth';
import { StorageError, StorageErrorType } from '@/utils/storage';

const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // State
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,

        // Actions
        login: async (email: string, password: string) => {
          set({ isLoading: true, error: null });
          try {
            const response = await authService.login(email, password);
            const { user } = response;

            // Token storage is now handled by authService internally
            // The authService.login method already stores tokens using the abstraction

            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } catch (error: any) {
            // Check if it's a storage error from authService
            if (error instanceof StorageError) {
              switch (error.type) {
                case StorageErrorType.QUOTA_EXCEEDED:
                  console.error('[AuthStore] Storage quota exceeded, cannot store auth token');
                  set({ error: 'Unable to save authentication. Storage quota exceeded.' });
                  break;
                case StorageErrorType.STORAGE_DISABLED:
                  console.warn('[AuthStore] Storage is disabled, authentication will not persist');
                  break;
                default:
                  console.error('[AuthStore] Storage error:', error);
              }
            }

            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: error.message || 'Login failed',
            });
            throw error;
          }
        },

        logout: async () => {
          set({ isLoading: true });
          try {
            await authService.logout();
          } catch (error) {
            console.error('Logout error:', error);
          } finally {
            // Token clearing is now handled by authService internally
            // The authService.logout method already clears tokens using the abstraction
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          }
        },

        refreshToken: async () => {
          try {
            const response = await authService.refreshToken();
            const { user } = response;

            // Token storage is now handled by authService internally
            // The authService.refreshToken method already updates tokens using the abstraction

            set({
              user,
              isAuthenticated: true,
              error: null,
            });
          } catch (error) {
            // If refresh fails, logout user
            get().logout();
            throw error;
          }
        },

        clearError: () => set({ error: null }),

        setUser: (user: User | null) => {
          set({
            user,
            isAuthenticated: !!user,
          });
        },
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    )
  )
);

export default useAuthStore;
