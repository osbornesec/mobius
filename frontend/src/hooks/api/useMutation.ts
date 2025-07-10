import { useMutation as useReactMutation, UseMutationOptions, UseMutationResult } from '@tanstack/react-query';
import { ApiError } from '@/services/api/config';
import useUIStore from '@/store/uiStore';

/**
 * Enhanced useMutation hook with automatic notifications
 */
export function useMutation<TData = unknown, TError = ApiError, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseMutationOptions<TData, TError, TVariables> & {
    successMessage?: string;
    errorMessage?: string;
    showNotification?: boolean;
  }
): UseMutationResult<TData, TError, TVariables> {
  const { addNotification } = useUIStore();
  const { successMessage, errorMessage, showNotification = true, ...mutationOptions } = options || {};

  return useReactMutation({
    mutationFn,
    onSuccess: (data, variables, context) => {
      if (showNotification && successMessage) {
        addNotification({
          type: 'success',
          title: 'Success',
          message: successMessage,
        });
      }
      mutationOptions.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      if (showNotification) {
        const message = errorMessage || (error as any)?.message || 'An error occurred';
        addNotification({
          type: 'error',
          title: 'Error',
          message,
        });
      }
      mutationOptions.onError?.(error, variables, context);
    },
    ...mutationOptions,
  });
}