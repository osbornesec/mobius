/**
 * Storage utility with comprehensive error handling and type safety
 * Provides a centralized abstraction for localStorage and sessionStorage operations
 */

// Storage error types
export enum StorageErrorType {
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  STORAGE_DISABLED = 'STORAGE_DISABLED',
  PARSE_ERROR = 'PARSE_ERROR',
  SERIALIZE_ERROR = 'SERIALIZE_ERROR',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  UNKNOWN = 'UNKNOWN',
}

export class StorageError extends Error {
  constructor(
    public type: StorageErrorType,
    message: string,
    public key?: string,
    public originalError?: unknown
  ) {
    super(message);
    this.name = 'StorageError';
  }
}

// Type-safe storage interface
interface StorageOperations {
  get<T>(key: string, defaultValue?: T): T | null;
  set<T>(key: string, value: T): void;
  remove(key: string): void;
  clear(): void;
  has(key: string): boolean;
  size(): number;
  getAllKeys(): string[];
}

// Logger interface for dependency injection
interface StorageLogger {
  debug(message: string, data?: any): void;
  info(message: string, data?: any): void;
  warn(message: string, data?: any): void;
  error(message: string, error?: any): void;
}

// Default console logger
const defaultLogger: StorageLogger = {
  debug: (message, data) => console.debug(`[Storage] ${message}`, data),
  info: (message, data) => console.info(`[Storage] ${message}`, data),
  warn: (message, data) => console.warn(`[Storage] ${message}`, data),
  error: (message, error) => console.error(`[Storage] ${message}`, error),
};

// Storage availability checker
function isStorageAvailable(type: 'localStorage' | 'sessionStorage'): boolean {
  try {
    const storage = window[type];
    const testKey = '__storage_test__';
    storage.setItem(testKey, 'test');
    storage.removeItem(testKey);
    return true;
  } catch (error) {
    return false;
  }
}

// Error detector to identify specific storage errors
function detectStorageError(error: unknown): StorageErrorType {
  if (error instanceof Error) {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();

    // Quota exceeded detection
    if (
      name === 'quotaexceedederror' ||
      message.includes('quota') ||
      message.includes('exceeded') ||
      (error as any).code === 22 // Legacy quota exceeded code
    ) {
      return StorageErrorType.QUOTA_EXCEEDED;
    }

    // Permission/security errors
    if (
      name === 'securityerror' ||
      message.includes('permission') ||
      message.includes('denied') ||
      message.includes('blocked')
    ) {
      return StorageErrorType.PERMISSION_DENIED;
    }

    // Parse errors
    if (name === 'syntaxerror' || message.includes('json') || message.includes('parse')) {
      return StorageErrorType.PARSE_ERROR;
    }
  }

  return StorageErrorType.UNKNOWN;
}

// Main storage class implementation
export class Storage implements StorageOperations {
  private storage: globalThis.Storage;
  private prefix: string;
  private logger: StorageLogger;
  private isAvailable: boolean;

  constructor(
    type: 'localStorage' | 'sessionStorage',
    options?: {
      prefix?: string;
      logger?: StorageLogger;
    }
  ) {
    this.storage = window[type];
    this.prefix = options?.prefix || '';
    this.logger = options?.logger || defaultLogger;
    this.isAvailable = isStorageAvailable(type);

    if (!this.isAvailable) {
      this.logger.warn(`${type} is not available. Storage operations will fail silently.`);
    }
  }

  private getKey(key: string): string {
    return this.prefix ? `${this.prefix}_${key}` : key;
  }

  get<T>(key: string, defaultValue?: T): T | null {
    const fullKey = this.getKey(key);

    if (!this.isAvailable) {
      this.logger.debug(`Storage not available, returning default for key: ${fullKey}`);
      return defaultValue ?? null;
    }

    try {
      const item = this.storage.getItem(fullKey);

      if (item === null) {
        this.logger.debug(`Key not found: ${fullKey}`);
        return defaultValue ?? null;
      }

      // Handle primitive strings that don't need parsing
      if (item === 'undefined' || item === 'null') {
        return defaultValue ?? null;
      }

      try {
        const parsed = JSON.parse(item);
        this.logger.debug(`Successfully retrieved key: ${fullKey}`);
        return parsed as T;
      } catch (parseError) {
        // If JSON parsing fails, return the raw string
        this.logger.debug(`Returning raw string for key: ${fullKey}`);
        return item as unknown as T;
      }
    } catch (error) {
      const errorType = detectStorageError(error);
      const storageError = new StorageError(
        errorType,
        `Failed to get item from storage: ${fullKey}`,
        fullKey,
        error
      );

      this.logger.error(storageError.message, {
        key: fullKey,
        errorType,
        originalError: error,
      });

      return defaultValue ?? null;
    }
  }

  set<T>(key: string, value: T): void {
    const fullKey = this.getKey(key);

    if (!this.isAvailable) {
      const error = new StorageError(
        StorageErrorType.STORAGE_DISABLED,
        'Storage is not available',
        fullKey
      );
      this.logger.error(error.message, error);
      throw error;
    }

    try {
      let serialized: string;

      // Handle different value types
      if (value === null || value === undefined) {
        serialized = 'null';
      } else if (typeof value === 'string') {
        // Store strings directly without JSON serialization
        serialized = value;
      } else {
        serialized = JSON.stringify(value);
      }

      this.storage.setItem(fullKey, serialized);
      this.logger.debug(`Successfully set key: ${fullKey}`, {
        valueType: typeof value,
        serializedLength: serialized.length,
      });
    } catch (error) {
      const errorType = detectStorageError(error);

      // Provide specific handling for quota exceeded
      if (errorType === StorageErrorType.QUOTA_EXCEEDED) {
        this.logger.error(`Storage quota exceeded for key: ${fullKey}`, {
          key: fullKey,
          approximateSize: JSON.stringify(value).length,
          suggestion: 'Consider clearing old data or using a different storage method',
        });
      }

      const storageError = new StorageError(
        errorType,
        `Failed to set item in storage: ${fullKey}`,
        fullKey,
        error
      );

      throw storageError;
    }
  }

  remove(key: string): void {
    const fullKey = this.getKey(key);

    if (!this.isAvailable) {
      this.logger.debug(`Storage not available, cannot remove key: ${fullKey}`);
      return;
    }

    try {
      this.storage.removeItem(fullKey);
      this.logger.debug(`Successfully removed key: ${fullKey}`);
    } catch (error) {
      const errorType = detectStorageError(error);
      this.logger.error(`Failed to remove key: ${fullKey}`, {
        errorType,
        originalError: error,
      });
    }
  }

  clear(): void {
    if (!this.isAvailable) {
      this.logger.debug('Storage not available, cannot clear');
      return;
    }

    try {
      if (this.prefix) {
        // Only clear items with our prefix
        const keys = this.getAllKeys();
        keys.forEach((key) => {
          this.storage.removeItem(this.getKey(key));
        });
        this.logger.info(`Cleared ${keys.length} items with prefix: ${this.prefix}`);
      } else {
        // Clear all storage
        this.storage.clear();
        this.logger.info('Cleared all storage items');
      }
    } catch (error) {
      const errorType = detectStorageError(error);
      this.logger.error('Failed to clear storage', {
        errorType,
        originalError: error,
      });
    }
  }

  has(key: string): boolean {
    const fullKey = this.getKey(key);

    if (!this.isAvailable) {
      return false;
    }

    try {
      return this.storage.getItem(fullKey) !== null;
    } catch (error) {
      this.logger.error(`Failed to check key existence: ${fullKey}`, error);
      return false;
    }
  }

  size(): number {
    if (!this.isAvailable) {
      return 0;
    }

    try {
      if (this.prefix) {
        return this.getAllKeys().length;
      }
      return this.storage.length;
    } catch (error) {
      this.logger.error('Failed to get storage size', error);
      return 0;
    }
  }

  getAllKeys(): string[] {
    if (!this.isAvailable) {
      return [];
    }

    try {
      const keys = [];
      const prefixLength = this.prefix.length;

      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key) {
          if (this.prefix) {
            if (key.startsWith(this.prefix + '_')) {
              keys.push(key.substring(prefixLength + 1));
            }
          } else {
            keys.push(key);
          }
        }
      }

      return keys;
    } catch (error) {
      this.logger.error('Failed to get all keys', error);
      return [];
    }
  }

  // Utility method to get storage usage info
  getStorageInfo(): {
    available: boolean;
    usage?: number;
    quota?: number;
    percentUsed?: number;
  } {
    if (!this.isAvailable) {
      return { available: false };
    }

    try {
      // Try to use navigator.storage.estimate() if available
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        navigator.storage.estimate().then((estimate) => {
          this.logger.info('Storage estimate:', {
            usage: estimate.usage,
            quota: estimate.quota,
            percentUsed: estimate.quota ? (estimate.usage! / estimate.quota) * 100 : 0,
          });
        });
      }

      // Calculate approximate storage size
      let totalSize = 0;
      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key) {
          const value = this.storage.getItem(key);
          if (value) {
            totalSize += key.length + value.length;
          }
        }
      }

      return {
        available: true,
        usage: totalSize,
        // Most browsers have 5-10MB limit for localStorage/sessionStorage
        quota: 5 * 1024 * 1024, // 5MB in bytes
        percentUsed: (totalSize / (5 * 1024 * 1024)) * 100,
      };
    } catch (error) {
      this.logger.error('Failed to get storage info', error);
      return { available: true };
    }
  }
}

// Pre-configured storage instances
export const localStorage = new Storage('localStorage', { prefix: 'mobius' });
export const sessionStorage = new Storage('sessionStorage', { prefix: 'mobius' });

// Backward-compatible storage functions for gradual migration
export const storage = {
  local: localStorage,
  session: sessionStorage,
};
