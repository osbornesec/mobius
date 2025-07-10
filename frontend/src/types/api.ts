/**
 * API-related type definitions
 */

// Pagination
export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// Sorting
export interface SortParams {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// Filtering
export interface FilterParams {
  search?: string;
  filters?: Record<string, any>;
}

// Combined query params
export type QueryParams = PaginationParams & SortParams & FilterParams;

// Error response
export interface ErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp?: string;
}

// File upload
export interface FileUploadResponse {
  url: string;
  filename: string;
  size: number;
  mimeType: string;
}