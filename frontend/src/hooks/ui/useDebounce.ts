import { useEffect, useState } from 'react';

/**
 * @description Returns a debounced version of the provided value, updating only after the specified delay has elapsed without further changes.
 *
 * @param value - The value to debounce. Can be of any type.
 * @param delay - The debounce delay in milliseconds.
 * @returns The latest debounced value, which updates after the delay period when the input value stops changing.
 *
 * @example
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 * // debouncedSearchTerm updates 300ms after the last change to searchTerm
 *
 * @since 1.0.0
 * Generated by CodeRabbit
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
