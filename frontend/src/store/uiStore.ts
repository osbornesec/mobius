import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { UIStore, Notification } from './types';

const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set, get) => ({
        // State
        theme: 'system',
        sidebarOpen: true,
        commandPaletteOpen: false,
        notifications: [],

        // Actions
        setTheme: (theme) => {
          set({ theme });
        },

        toggleSidebar: () => {
          set((state) => ({ sidebarOpen: !state.sidebarOpen }));
        },

        setSidebarOpen: (open) => {
          set({ sidebarOpen: open });
        },

        toggleCommandPalette: () => {
          set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen }));
        },

        setCommandPaletteOpen: (open) => {
          set({ commandPaletteOpen: open });
        },

        addNotification: (notification) => {
          const id = Math.random().toString(36).substr(2, 9);
          const newNotification: Notification = {
            ...notification,
            id,
            createdAt: Date.now(),
          };

          set((state) => ({
            notifications: [...state.notifications, newNotification],
          }));

          return id; // Return the ID so consumers can manage removal
        },

        removeNotification: (id) => {
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }));
        },

        clearNotifications: () => {
          set({ notifications: [] });
        },
      }),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
          sidebarOpen: state.sidebarOpen,
        }),
      }
    )
  )
);

export default useUIStore;
