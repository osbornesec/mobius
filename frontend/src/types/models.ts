/**
 * Domain model type definitions
 */

export interface Project {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  collaborators: string[];
  tags: string[];
  settings: ProjectSettings;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectSettings {
  isPublic: boolean;
  defaultBranch: string;
  enableVersioning: boolean;
  autoSave: boolean;
  customSettings?: Record<string, any>;
}

export interface Document {
  id: string;
  projectId: string;
  contextId: string;
  name: string;
  content: string;
  mimeType: string;
  size: number;
  path: string;
  metadata: DocumentMetadata;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentMetadata {
  language?: string;
  encoding?: string;
  lineCount?: number;
  wordCount?: number;
  tags?: string[];
  [key: string]: any;
}

export interface VectorEmbedding {
  id: string;
  documentId: string;
  contextId: string;
  chunk: string;
  embedding: number[];
  metadata: EmbeddingMetadata;
  createdAt: string;
}

export interface EmbeddingMetadata {
  model: string;
  dimensions: number;
  chunkIndex: number;
  totalChunks: number;
  [key: string]: any;
}

export interface Activity {
  id: string;
  userId: string;
  action: ActivityAction;
  resourceType: 'project' | 'context' | 'document';
  resourceId: string;
  details: Record<string, any>;
  timestamp: string;
}

export type ActivityAction = 
  | 'created' 
  | 'updated' 
  | 'deleted' 
  | 'shared' 
  | 'exported' 
  | 'imported'
  | 'duplicated';

export interface Permission {
  id: string;
  userId: string;
  resourceType: 'project' | 'context';
  resourceId: string;
  level: PermissionLevel;
  grantedBy: string;
  grantedAt: string;
}

export type PermissionLevel = 'read' | 'write' | 'admin';

export interface ApiKey {
  id: string;
  name: string;
  key: string; // Only shown once after creation
  userId: string;
  permissions: string[];
  expiresAt?: string;
  lastUsedAt?: string;
  createdAt: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  version: string;
  uptime: number;
  services: {
    database: ServiceStatus;
    redis: ServiceStatus;
    vectorDb: ServiceStatus;
    storage: ServiceStatus;
  };
  metrics: {
    cpu: number;
    memory: number;
    diskSpace: number;
    activeConnections: number;
  };
}

export interface ServiceStatus {
  status: 'up' | 'down';
  latency?: number;
  error?: string;
}