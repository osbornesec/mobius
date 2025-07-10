import { format, formatDistance, formatRelative, isValid, parseISO } from 'date-fns';

/**
 * Format a date string or Date object
 * @param date - Date string or Date object
 * @param formatStr - Format string (default: 'PPP')
 * @returns Formatted date string
 */
export function formatDate(date: string | Date, formatStr: string = 'PPP'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) {
    return 'Invalid date';
  }
  
  return format(dateObj, formatStr);
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 * @param date - Date string or Date object
 * @param baseDate - Base date to compare against (default: now)
 * @returns Relative time string
 */
export function formatRelativeTime(date: string | Date, baseDate: Date = new Date()): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) {
    return 'Invalid date';
  }
  
  return formatDistance(dateObj, baseDate, { addSuffix: true });
}

/**
 * Format a date as relative with automatic formatting based on distance
 * @param date - Date string or Date object
 * @param baseDate - Base date to compare against (default: now)
 * @returns Formatted date string
 */
export function formatRelativeDate(date: string | Date, baseDate: Date = new Date()): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  if (!isValid(dateObj)) {
    return 'Invalid date';
  }
  
  return formatRelative(dateObj, baseDate);
}

/**
 * Format a date for display in tables or lists
 * @param date - Date string or Date object
 * @returns Formatted date string
 */
export function formatTableDate(date: string | Date): string {
  return formatDate(date, 'MMM d, yyyy');
}

/**
 * Format a date with time
 * @param date - Date string or Date object
 * @returns Formatted date string with time
 */
export function formatDateTime(date: string | Date): string {
  return formatDate(date, 'PPP p');
}

/**
 * Format a date for API requests (ISO string)
 * @param date - Date object
 * @returns ISO date string
 */
export function formatForAPI(date: Date): string {
  return date.toISOString();
}