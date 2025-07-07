# Mobius

This project was initialized by Gemini.

## Project Structure

The Mobius project follows a hybrid architecture with both frontend (React/TypeScript) and backend (FastAPI/Python) components:

```
Mobius/
├── .claude/                    # Claude AI assistant configuration
│   ├── commands/              # Custom Claude commands
│   └── hooks/                 # Claude hooks
├── ai_docs/                   # AI-generated documentation and planning
│   ├── Research/              # Research documents
│   └── planning/              # Project planning documents
├── alembic/                   # Database migration management
│   └── versions/              # Database migration version files
├── app/                       # Backend application (FastAPI)
│   ├── api/                   # API layer
│   │   └── v1/               # API version 1
│   │       └── endpoints/     # API endpoint handlers
│   ├── core/                  # Core functionality (config, security, etc.)
│   ├── models/                # Data models
│   │   ├── database/          # Database ORM models
│   │   ├── domain/            # Domain/business logic models
│   │   └── schemas/           # Pydantic schemas
│   │       ├── request/       # Request schemas
│   │       └── response/      # Response schemas
│   ├── processing/            # Data processing modules
│   │   ├── chunkers/          # Text chunking algorithms
│   │   ├── embedders/         # Embedding generation
│   │   └── parsers/           # File parsers
│   ├── repositories/          # Database repositories
│   ├── services/              # Business logic services
│   └── utils/                 # Backend utility functions
├── docker/                    # Docker configuration files
├── docs/                      # Project documentation
├── public/                    # Frontend static assets
├── scripts/                   # Build and utility scripts
│   ├── backend/              # Backend-specific scripts
│   └── frontend/             # Frontend-specific scripts
├── src/                       # Frontend application (React)
│   ├── components/            # Reusable React components
│   ├── pages/                # Application pages/routes
│   ├── styles/               # CSS and styling files
│   └── utils/                # Frontend utility functions
├── tests/                     # Test suite
│   ├── backend/              # Backend tests
│   │   ├── e2e/              # End-to-end tests
│   │   ├── integration/      # Integration tests
│   │   └── unit/             # Unit tests
│   └── frontend/             # Frontend tests
├── CLAUDE.md                 # Claude AI instructions
├── GEMINI.md                 # Gemini AI instructions
├── README.md                 # Project description (this file)
├── .gitignore               # Git ignore configuration
└── package.json             # Frontend dependencies and scripts
```

### Directory Descriptions

#### Backend (Python/FastAPI)
- **`app/`**: Main backend application directory containing the FastAPI application
  - **`api/`**: REST API endpoints organized by version
  - **`core/`**: Core functionality including configuration, security, and database setup
  - **`models/`**: All data models organized into database models, domain models, and API schemas
  - **`processing/`**: Data processing pipeline components for handling documents
  - **`repositories/`**: Data access layer following the repository pattern
  - **`services/`**: Business logic layer
  - **`utils/`**: Shared utility functions

- **`alembic/`**: Database migration management using Alembic
- **`docker/`**: Docker configuration for containerized deployment

#### Frontend (React/TypeScript)
- **`src/`**: Main frontend application directory
  - **`components/`**: Reusable UI components
  - **`pages/`**: Application pages/routes
  - **`styles/`**: CSS and styling files
  - **`utils/`**: Frontend utility functions
- **`public/`**: Static assets like images, fonts, etc.

#### Configuration & Documentation
- **`.claude/`**: Configuration for Claude AI assistant integration
- **`ai_docs/`**: AI-generated documentation, research, and planning materials
- **`docs/`**: General project documentation
- **`scripts/`**: Build and utility scripts separated by backend/frontend

#### Testing
- **`tests/`**: Comprehensive test suite
  - **`backend/`**: Backend tests organized by type (unit, integration, e2e)
  - **`frontend/`**: Frontend component and integration tests

This structure supports a scalable Context Engineering Platform with clear separation between frontend and backend concerns, comprehensive testing, and proper documentation.
