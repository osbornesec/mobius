/**
 * Storage diagnostics utility for debugging storage-related issues
 * Provides comprehensive information about storage state and capabilities
 */

import { localStorage, sessionStorage, StorageError, StorageErrorType } from './storage';

export interface StorageDiagnostics {
  localStorageAvailable: boolean;
  sessionStorageAvailable: boolean;
  localStorageInfo: {
    itemCount: number;
    estimatedSize: number;
    quotaPercentage: number;
    largestItems: Array<{ key: string; size: number }>;
  };
  sessionStorageInfo: {
    itemCount: number;
    estimatedSize: number;
    quotaPercentage: number;
    largestItems: Array<{ key: string; size: number }>;
  };
  browserInfo: {
    userAgent: string;
    cookiesEnabled: boolean;
    onLine: boolean;
    storageQuota?: {
      usage?: number;
      quota?: number;
    };
  };
  errors: Array<{
    storage: 'local' | 'session';
    operation: string;
    error: string;
    type?: StorageErrorType;
  }>;
}

/**
 * Run comprehensive storage diagnostics
 */
export async function runStorageDiagnostics(): Promise<StorageDiagnostics> {
  const diagnostics: StorageDiagnostics = {
    localStorageAvailable: false,
    sessionStorageAvailable: false,
    localStorageInfo: {
      itemCount: 0,
      estimatedSize: 0,
      quotaPercentage: 0,
      largestItems: [],
    },
    sessionStorageInfo: {
      itemCount: 0,
      estimatedSize: 0,
      quotaPercentage: 0,
      largestItems: [],
    },
    browserInfo: {
      userAgent: navigator.userAgent,
      cookiesEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
    },
    errors: [],
  };

  // Check localStorage availability
  try {
    localStorage.set('__diagnostic_test__', 'test');
    localStorage.remove('__diagnostic_test__');
    diagnostics.localStorageAvailable = true;
  } catch (error) {
    diagnostics.errors.push({
      storage: 'local',
      operation: 'availability_test',
      error: error instanceof Error ? error.message : 'Unknown error',
      type: error instanceof StorageError ? error.type : undefined,
    });
  }

  // Check sessionStorage availability
  try {
    sessionStorage.set('__diagnostic_test__', 'test');
    sessionStorage.remove('__diagnostic_test__');
    diagnostics.sessionStorageAvailable = true;
  } catch (error) {
    diagnostics.errors.push({
      storage: 'session',
      operation: 'availability_test',
      error: error instanceof Error ? error.message : 'Unknown error',
      type: error instanceof StorageError ? error.type : undefined,
    });
  }

  // Get localStorage info
  if (diagnostics.localStorageAvailable) {
    try {
      const info = localStorage.getStorageInfo();
      const keys = localStorage.getAllKeys();
      const itemSizes = [];

      for (const key of keys) {
        try {
          const value = localStorage.get(key);
          const size = JSON.stringify(value).length;
          itemSizes.push({ key, size });
        } catch (error) {
          diagnostics.errors.push({
            storage: 'local',
            operation: `get_item_size_${key}`,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      }

      // Sort by size and get top 5
      itemSizes.sort((a, b) => b.size - a.size);

      diagnostics.localStorageInfo = {
        itemCount: keys.length,
        estimatedSize: info.usage || itemSizes.reduce((sum, item) => sum + item.size, 0),
        quotaPercentage: info.percentUsed || 0,
        largestItems: itemSizes.slice(0, 5),
      };
    } catch (error) {
      diagnostics.errors.push({
        storage: 'local',
        operation: 'get_storage_info',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  // Get sessionStorage info
  if (diagnostics.sessionStorageAvailable) {
    try {
      const info = sessionStorage.getStorageInfo();
      const keys = sessionStorage.getAllKeys();
      const itemSizes = [];

      for (const key of keys) {
        try {
          const value = sessionStorage.get(key);
          const size = JSON.stringify(value).length;
          itemSizes.push({ key, size });
        } catch (error) {
          diagnostics.errors.push({
            storage: 'session',
            operation: `get_item_size_${key}`,
            error: error instanceof Error ? error.message : 'Unknown error',
          });
        }
      }

      // Sort by size and get top 5
      itemSizes.sort((a, b) => b.size - a.size);

      diagnostics.sessionStorageInfo = {
        itemCount: keys.length,
        estimatedSize: info.usage || itemSizes.reduce((sum, item) => sum + item.size, 0),
        quotaPercentage: info.percentUsed || 0,
        largestItems: itemSizes.slice(0, 5),
      };
    } catch (error) {
      diagnostics.errors.push({
        storage: 'session',
        operation: 'get_storage_info',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  // Get browser storage quota if available
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    try {
      const estimate = await navigator.storage.estimate();
      diagnostics.browserInfo.storageQuota = {
        usage: estimate.usage,
        quota: estimate.quota,
      };
    } catch (error) {
      diagnostics.errors.push({
        storage: 'local',
        operation: 'get_browser_quota',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  return diagnostics;
}

/**
 * Log storage diagnostics to console
 */
export async function logStorageDiagnostics(): Promise<void> {
  const diagnostics = await runStorageDiagnostics();

  console.group(
    '%c📊 Storage Diagnostics Report',
    'color: #3498db; font-weight: bold; font-size: 16px'
  );

  // Availability
  console.group('%c🔍 Storage Availability', 'color: #2ecc71; font-weight: bold');
  console.log(
    'LocalStorage:',
    diagnostics.localStorageAvailable ? '✅ Available' : '❌ Not Available'
  );
  console.log(
    'SessionStorage:',
    diagnostics.sessionStorageAvailable ? '✅ Available' : '❌ Not Available'
  );
  console.groupEnd();

  // LocalStorage Info
  if (diagnostics.localStorageAvailable) {
    console.group('%c💾 LocalStorage Info', 'color: #e74c3c; font-weight: bold');
    console.log('Item Count:', diagnostics.localStorageInfo.itemCount);
    console.log('Estimated Size:', formatBytes(diagnostics.localStorageInfo.estimatedSize));
    console.log('Quota Usage:', `${diagnostics.localStorageInfo.quotaPercentage.toFixed(2)}%`);
    if (diagnostics.localStorageInfo.largestItems.length > 0) {
      console.group('Largest Items:');
      diagnostics.localStorageInfo.largestItems.forEach((item) => {
        console.log(`${item.key}: ${formatBytes(item.size)}`);
      });
      console.groupEnd();
    }
    console.groupEnd();
  }

  // SessionStorage Info
  if (diagnostics.sessionStorageAvailable) {
    console.group('%c💾 SessionStorage Info', 'color: #f39c12; font-weight: bold');
    console.log('Item Count:', diagnostics.sessionStorageInfo.itemCount);
    console.log('Estimated Size:', formatBytes(diagnostics.sessionStorageInfo.estimatedSize));
    console.log('Quota Usage:', `${diagnostics.sessionStorageInfo.quotaPercentage.toFixed(2)}%`);
    if (diagnostics.sessionStorageInfo.largestItems.length > 0) {
      console.group('Largest Items:');
      diagnostics.sessionStorageInfo.largestItems.forEach((item) => {
        console.log(`${item.key}: ${formatBytes(item.size)}`);
      });
      console.groupEnd();
    }
    console.groupEnd();
  }

  // Browser Info
  console.group('%c🌐 Browser Info', 'color: #9b59b6; font-weight: bold');
  console.log('User Agent:', diagnostics.browserInfo.userAgent);
  console.log('Cookies Enabled:', diagnostics.browserInfo.cookiesEnabled ? '✅' : '❌');
  console.log('Online:', diagnostics.browserInfo.onLine ? '✅' : '❌');
  if (diagnostics.browserInfo.storageQuota) {
    console.log('Browser Storage Quota:', {
      usage: formatBytes(diagnostics.browserInfo.storageQuota.usage || 0),
      quota: formatBytes(diagnostics.browserInfo.storageQuota.quota || 0),
      percentUsed: diagnostics.browserInfo.storageQuota.quota
        ? (
            ((diagnostics.browserInfo.storageQuota.usage || 0) /
              diagnostics.browserInfo.storageQuota.quota) *
            100
          ).toFixed(2) + '%'
        : 'N/A',
    });
  }
  console.groupEnd();

  // Errors
  if (diagnostics.errors.length > 0) {
    console.group('%c⚠️ Errors Detected', 'color: #e74c3c; font-weight: bold');
    diagnostics.errors.forEach((error) => {
      console.error(
        `[${error.storage}] ${error.operation}:`,
        error.error,
        error.type ? `(Type: ${error.type})` : ''
      );
    });
    console.groupEnd();
  }

  console.groupEnd();
}

/**
 * Format bytes to human readable format
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Clear storage with logging
 */
export async function clearStorageWithDiagnostics(
  type: 'local' | 'session' | 'both' = 'both'
): Promise<void> {
  console.group('%c🧹 Clearing Storage', 'color: #e74c3c; font-weight: bold');

  // Run diagnostics before clearing
  const beforeDiagnostics = await runStorageDiagnostics();
  console.log('Before clearing:', {
    localStorage: `${beforeDiagnostics.localStorageInfo.itemCount} items, ${formatBytes(beforeDiagnostics.localStorageInfo.estimatedSize)}`,
    sessionStorage: `${beforeDiagnostics.sessionStorageInfo.itemCount} items, ${formatBytes(beforeDiagnostics.sessionStorageInfo.estimatedSize)}`,
  });

  // Clear storage
  if (type === 'local' || type === 'both') {
    try {
      localStorage.clear();
      console.log('✅ LocalStorage cleared');
    } catch (error) {
      console.error('❌ Failed to clear LocalStorage:', error);
    }
  }

  if (type === 'session' || type === 'both') {
    try {
      sessionStorage.clear();
      console.log('✅ SessionStorage cleared');
    } catch (error) {
      console.error('❌ Failed to clear SessionStorage:', error);
    }
  }

  // Run diagnostics after clearing
  const afterDiagnostics = await runStorageDiagnostics();
  console.log('After clearing:', {
    localStorage: `${afterDiagnostics.localStorageInfo.itemCount} items, ${formatBytes(afterDiagnostics.localStorageInfo.estimatedSize)}`,
    sessionStorage: `${afterDiagnostics.sessionStorageInfo.itemCount} items, ${formatBytes(afterDiagnostics.sessionStorageInfo.estimatedSize)}`,
  });

  console.groupEnd();
}

// Export to window for easy debugging in production
if (typeof window !== 'undefined') {
  (window as any).storageDiagnostics = {
    run: runStorageDiagnostics,
    log: logStorageDiagnostics,
    clear: clearStorageWithDiagnostics,
  };
}
