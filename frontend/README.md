# Mobius Frontend

## Overview

The Mobius frontend is a modern React application built with TypeScript, Vite, and Zustand for state management. It provides a user interface for the Context Engineering Platform.

## Tech Stack

- **React 18+** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Zustand** - State management
- **React Query** - Server state management
- **React Router** - Routing
- **Tailwind CSS** - Styling
- **Vitest** - Testing
- **Socket.io Client** - WebSocket communication

## Project Structure

```
frontend/
├── src/
│   ├── assets/         # Static assets (images, icons, styles)
│   ├── components/     # Reusable React components
│   │   ├── ui/        # Base UI components
│   │   ├── common/    # Common components
│   │   └── features/  # Feature-specific components
│   ├── hooks/         # Custom React hooks
│   │   ├── api/      # API-related hooks
│   │   ├── ui/       # UI-related hooks
│   │   └── utils/    # Utility hooks
│   ├── layouts/       # Page layouts
│   ├── pages/         # Page components
│   ├── services/      # API and external services
│   │   ├── api/      # API client and services
│   │   └── websocket/ # WebSocket client
│   ├── store/         # Zustand stores
│   ├── types/         # TypeScript type definitions
│   ├── utils/         # Utility functions
│   │   ├── constants/ # Application constants
│   │   ├── formatting/ # Formatting utilities
│   │   └── validation/ # Validation schemas
│   └── test/          # Test utilities and setup
├── public/            # Public assets
├── .env.example       # Environment variables example
├── package.json       # Dependencies and scripts
├── tsconfig.json      # TypeScript configuration
├── vite.config.ts     # Vite configuration
└── vitest.config.ts   # Vitest configuration
```

## Getting Started

### Prerequisites

- Node.js 20+
- npm 10+

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at http://localhost:3000

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=Mobius
VITE_APP_VERSION=0.1.0
VITE_ENVIRONMENT=development
```

## State Management

The application uses Zustand for state management with the following stores:

### AuthStore
- Manages user authentication state
- Handles login/logout operations
- Persists authentication state

### ContextStore
- Manages context data
- Handles CRUD operations for contexts

### UIStore
- Manages UI state (theme, sidebar, notifications)
- Persists user preferences

## API Integration

API services are organized in `src/services/api/`:

- **auth.ts** - Authentication services
- **context.ts** - Context management services
- **config.ts** - Axios configuration and interceptors

## Testing

Run tests:
```bash
npm run test
```

Run tests with coverage:
```bash
npm run test:coverage
```

Run tests in watch mode:
```bash
npm run test:watch
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run typecheck` - Run TypeScript type checking

## Code Style

The project uses:
- ESLint for linting
- Prettier for code formatting
- TypeScript strict mode

## Contributing

1. Follow the existing code structure
2. Write tests for new features
3. Ensure all tests pass
4. Run linting and formatting before committing