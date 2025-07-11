import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { ContextStore, Context } from './types';
import { contextService } from '@/services/api/context';

const useContextStore = create<ContextStore>()(
  devtools(
    (set, get) => ({
      // State
      contexts: [],
      activeContext: null,
      isLoading: false,
      error: null,

      // Actions
      fetchContexts: async (projectId: string) => {
        set({ isLoading: true, error: null });
        try {
          const contexts = await contextService.getContexts(projectId);
          set({
            contexts,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            contexts: [],
            isLoading: false,
            error: error.message || 'Failed to fetch contexts',
          });
          throw error;
        }
      },

      createContext: async (contextData: Omit<Context, 'id' | 'createdAt' | 'updatedAt'>) => {
        set({ isLoading: true, error: null });
        try {
          const newContext = await contextService.createContext(contextData);
          set((state) => ({
            contexts: [...state.contexts, newContext],
            isLoading: false,
            error: null,
          }));
          return newContext;
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to create context',
          });
          throw error;
        }
      },

      updateContext: async (id: string, updates: Partial<Context>) => {
        set({ isLoading: true, error: null });
        try {
          const updatedContext = await contextService.updateContext(id, updates);
          set((state) => ({
            contexts: state.contexts.map((ctx) =>
              ctx.id === id ? updatedContext : ctx
            ),
            activeContext:
              state.activeContext?.id === id ? updatedContext : state.activeContext,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to update context',
          });
          throw error;
        }
      },

      deleteContext: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          await contextService.deleteContext(id);
          set((state) => ({
            contexts: state.contexts.filter((ctx) => ctx.id !== id),
            activeContext:
              state.activeContext?.id === id ? null : state.activeContext,
            isLoading: false,
            error: null,
          }));
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.message || 'Failed to delete context',
          });
          throw error;
        }
      },

      setActiveContext: (context: Context | null) => {
        set({ activeContext: context });
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'context-store',
    }
  )
);

export default useContextStore;
