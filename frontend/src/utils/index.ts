// Export storage utilities
export * from './storage';
export * from './storageDiagnostics';

// Re-export commonly used utilities
export { localStorage, sessionStorage, storage } from './storage';
export { logStorageDiagnostics, clearStorageWithDiagnostics } from './storageDiagnostics';
