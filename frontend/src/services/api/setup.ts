import { useNavigate } from 'react-router-dom';
import { setNavigateToLogin } from './config';

/**
 * Hook to set up API navigation helpers.
 * This should be called in the root App component to enable proper router-based navigation
 * from within API interceptors, preventing direct window.location manipulation.
 */
export const useApiSetup = () => {
  const navigate = useNavigate();

  // Set up the navigation helper for redirecting to login
  setNavigateToLogin(() => {
    navigate('/login', { replace: true });
  });
};
