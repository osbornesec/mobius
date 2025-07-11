import apiClient, { ApiResponse, createRequest } from './config';
import { Context } from '@/store/types';

export interface CreateContextRequest {
  name: string;
  description?: string;
  projectId: string;
  version: string;
  metadata?: Record<string, any>;
}

export interface UpdateContextRequest {
  name?: string;
  description?: string;
  version?: string;
  metadata?: Record<string, any>;
}

export interface ContextSearchParams {
  projectId?: string;
  name?: string;
  version?: string;
  limit?: number;
  offset?: number;
}

class ContextService {
  async getContexts(projectId: string): Promise<Context[]> {
    const response = await apiClient.get<ApiResponse<Context[]>>(`/contexts`, {
      params: { projectId },
    });
    return response.data.data;
  }

  async getContext(id: string): Promise<Context> {
    const response = await apiClient.get<ApiResponse<Context>>(`/contexts/${id}`);
    return response.data.data;
  }

  async createContext(data: CreateContextRequest): Promise<Context> {
    const response = await apiClient.post<ApiResponse<Context>>('/contexts', data);
    return response.data.data;
  }

  async updateContext(id: string, updates: UpdateContextRequest): Promise<Context> {
    const response = await apiClient.patch<ApiResponse<Context>>(`/contexts/${id}`, updates);
    return response.data.data;
  }

  async deleteContext(id: string): Promise<void> {
    await apiClient.delete(`/contexts/${id}`);
  }

  async searchContexts(params: ContextSearchParams): Promise<Context[]> {
    const response = await apiClient.get<ApiResponse<Context[]>>('/contexts/search', {
      params,
    });
    return response.data.data;
  }

  async duplicateContext(id: string, name: string): Promise<Context> {
    const response = await apiClient.post<ApiResponse<Context>>(`/contexts/${id}/duplicate`, {
      name,
    });
    return response.data.data;
  }

  async exportContext(id: string): Promise<Blob> {
    const response = await apiClient.get(
      `/contexts/${id}/export`,
      createRequest({
        responseType: 'blob',
        operationType: 'LONG_RUNNING', // Export might take time
      })
    );
    return response.data;
  }

  async importContext(file: File, projectId: string): Promise<Context> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('projectId', projectId);

    const response = await apiClient.post<ApiResponse<Context>>(
      '/contexts/import',
      formData,
      createRequest({
        // Don't set Content-Type header - browser will set it automatically with boundary
        operationType: 'LONG_RUNNING', // File upload might take time
      })
    );
    return response.data.data;
  }
}

export const contextService = new ContextService();
