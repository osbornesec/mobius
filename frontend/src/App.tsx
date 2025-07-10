import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';

// Layouts
import MainLayout from '@/layouts/MainLayout';

// Pages
import Dashboard from '@/pages/Dashboard';

// Stores
import useAuthStore from '@/store/authStore';
import useUIStore from '@/store/uiStore';

// Constants
import { APP_ROUTES } from '@/utils/constants';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

function App() {
  const { theme, setTheme } = useUIStore();
  const { isAuthenticated } = useAuthStore();

  // Apply theme on mount and when it changes
  useEffect(() => {
    const root = document.documentElement;

    if (
      theme === 'dark' ||
      (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    ) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === 'system') {
        if (e.matches) {
          root.classList.add('dark');
        } else {
          root.classList.remove('dark');
        }
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path={APP_ROUTES.LOGIN} element={<div>Login Page</div>} />
          <Route path={APP_ROUTES.REGISTER} element={<div>Register Page</div>} />

          {/* Protected routes */}
          <Route element={<MainLayout />}>
            <Route
              path={APP_ROUTES.HOME}
              element={
                isAuthenticated ? (
                  <Navigate to={APP_ROUTES.DASHBOARD} replace />
                ) : (
                  <Navigate to={APP_ROUTES.LOGIN} replace />
                )
              }
            />
            <Route path={APP_ROUTES.DASHBOARD} element={<Dashboard />} />
            <Route path={APP_ROUTES.PROJECTS} element={<div>Projects Page</div>} />
            <Route path={APP_ROUTES.CONTEXTS} element={<div>Contexts Page</div>} />
            <Route path={APP_ROUTES.SETTINGS} element={<div>Settings Page</div>} />
            <Route path={APP_ROUTES.PROFILE} element={<div>Profile Page</div>} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<div>404 - Page Not Found</div>} />
        </Routes>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 5000,
            style: {
              background: theme === 'dark' ? '#1F2937' : '#FFFFFF',
              color: theme === 'dark' ? '#F9FAFB' : '#111827',
            },
          }}
        />
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
