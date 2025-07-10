import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi, beforeEach } from 'vitest';

// Store reset functions for Zustand stores
const storeResetFns = new Set<() => void>();

// Mock Zustand
vi.mock('zustand', async () => {
  const { create: actualCreate, createStore: actualCreateStore } =
    await vi.importActual<typeof import('zustand')>('zustand');

  // Mock create function
  const create = (<T>(stateCreator: any) => {
    const store = actualCreate(stateCreator);
    const initialState = store.getState();
    storeResetFns.add(() => {
      store.setState(initialState, true);
    });
    return store;
  }) as typeof actualCreate;

  // Mock createStore function
  const createStore = (<T>(stateCreator: any) => {
    const store = actualCreateStore(stateCreator);
    const initialState = store.getInitialState();
    storeResetFns.add(() => {
      store.setState(initialState, true);
    });
    return store;
  }) as typeof actualCreateStore;

  return { create, createStore };
});

// Cleanup after each test case
afterEach(() => {
  cleanup();
  // Reset all Zustand stores
  storeResetFns.forEach((resetFn) => resetFn());
});

// Setup localStorage mock
beforeEach(() => {
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  };
  global.localStorage = localStorageMock as any;
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  root = null;
  rootMargin = '';
  thresholds = [];

  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return [];
  }
} as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;
