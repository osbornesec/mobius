import { useQuery as useReactQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { ApiError } from '@/services/api/config';

/**
 * Enhanced useQuery hook with error handling and typing
 */
export function useQuery<TData = unknown, TError = ApiError>(
  queryKey: any[],
  queryFn: () => Promise<TData>,
  options?: Omit<UseQueryOptions<TData, TError>, 'queryKey' | 'queryFn'>
): UseQueryResult<TData, TError> {
  return useReactQuery({
    queryKey,
    queryFn,
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error instanceof AxiosError && error.response?.status && error.response.status >= 400 && error.response.status < 500) {
        return false;
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
    ...options,
  });
}