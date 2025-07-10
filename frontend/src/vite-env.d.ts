/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_ENVIRONMENT: 'development' | 'staging' | 'production'
  readonly VITE_SENTRY_DSN?: string
  readonly VITE_GOOGLE_ANALYTICS_ID?: string
  readonly VITE_FEATURE_FLAGS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}