import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { AuthStore, User } from './types';
import { authService } from '@/services/api/auth';

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
            const { user, token } = response;
            
            // Store token in localStorage
            localStorage.setItem('authToken', token);
            
            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } catch (error: any) {
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
            // Clear token and reset state
            localStorage.removeItem('authToken');
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
            const { user, token } = response;
            
            localStorage.setItem('authToken', token);
            
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