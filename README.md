# Mobius

This project was initialized by Gemini.

## Project Structure

The Mobius Context Engineering Platform follows a comprehensive architecture with both frontend (React/TypeScript) and backend (FastAPI/Python) components, designed for scalability and multi-agent AI integration:

```
Mobius/
├── .claude/                    # Claude AI assistant configuration
│   ├── commands/              # Custom Claude commands
│   ├── hooks/                 # Claude hooks
│   └── sessions/              # Session management
├── .github/                   # GitHub configuration
│   ├── workflows/             # CI/CD workflows
│   └── ISSUE_TEMPLATE/        # Issue templates
├── ai_docs/                   # AI-generated documentation and planning
│   ├── Research/              # Research documents
│   ├── planning/              # Project planning documents
│   └── tasks/                 # Development task specifications
├── alembic/                   # Database migration management
│   └── versions/              # Database migration version files
├── app/                       # Backend application (FastAPI)
│   ├── agents/                # Multi-agent system components
│   │   ├── base_agent.py     # Base agent class
│   │   ├── context_builder/   # Context builder agent
│   │   ├── retrieval/         # Retrieval agent
│   │   ├── code_generator/    # Code generation agent
│   │   └── orchestrator/      # Agent orchestration
│   ├── analytics/             # Analytics and monitoring
│   │   ├── collectors/        # Data collectors
│   │   ├── metrics/           # Metrics definitions
│   │   └── reporting/         # Reporting modules
│   ├── api/                   # API layer
│   │   └── v1/               # API version 1
│   │       ├── endpoints/     # API endpoint handlers
│   │       ├── middleware/    # API middleware
│   │       └── websockets/    # WebSocket handlers
│   ├── core/                  # Core functionality
│   │   ├── config.py         # Configuration management
│   │   ├── security.py       # Security utilities
│   │   ├── database.py       # Database setup
│   │   └── logging.py        # Logging configuration
│   ├── integrations/          # External integrations
│   │   ├── openai/           # OpenAI integration
│   │   ├── anthropic/        # Anthropic integration
│   │   ├── github/           # GitHub integration
│   │   └── vscode/           # VSCode/LSP integration
│   ├── models/                # Data models
│   │   ├── database/          # Database ORM models
│   │   ├── domain/            # Domain/business logic models
│   │   └── schemas/           # Pydantic schemas
│   │       ├── request/       # Request schemas
│   │       └── response/      # Response schemas
│   ├── processing/            # Data processing modules
│   │   ├── chunkers/          # Text chunking algorithms
│   │   ├── embedders/         # Embedding generation
│   │   ├── parsers/           # File parsers
│   │   └── pipelines/         # Processing pipelines
│   ├── repositories/          # Database repositories
│   ├── services/              # Business logic services
│   │   ├── agent_coordinator/ # Agent coordination service
│   │   ├── context_engine/    # Context management
│   │   ├── prompt_engine/     # Prompt engineering
│   │   ├── response_formatter/# Response formatting
│   │   └── vector_store/      # Vector storage operations
│   ├── storage/               # Storage backends
│   │   ├── vector/            # Vector database interfaces
│   │   ├── object/            # Object storage (S3, GCS)
│   │   └── cache/             # Caching layer
│   ├── utils/                 # Backend utility functions
│   │   ├── semantic_analyzer/ # Semantic analysis utilities
│   │   └── validators/        # Input validators
│   └── main.py               # FastAPI application entry point
├── docker/                    # Docker configuration files
│   ├── backend/              # Backend Docker configs
│   ├── frontend/             # Frontend Docker configs
│   └── nginx/                # Nginx configurations
├── docs/                      # Project documentation
│   ├── api/                  # API documentation
│   ├── architecture/         # Architecture diagrams
│   └── deployment/           # Deployment guides
├── e2e/                       # End-to-end tests
│   ├── cypress/              # Cypress E2E tests
│   └── playwright/           # Playwright tests
├── infrastructure/            # Infrastructure as Code
│   ├── kubernetes/           # Kubernetes manifests
│   │   ├── base/            # Base configurations
│   │   └── overlays/        # Environment overlays
│   ├── terraform/            # Terraform configurations
│   └── helm/                 # Helm charts
├── public/                    # Frontend static assets
├── scripts/                   # Build and utility scripts
│   ├── backend/              # Backend-specific scripts
│   ├── frontend/             # Frontend-specific scripts
│   ├── deployment/           # Deployment scripts
│   └── monitoring/           # Monitoring setup scripts
├── src/                       # Frontend application (React)
│   ├── api/                  # API client
│   ├── components/           # Reusable React components
│   │   ├── common/          # Common UI components
│   │   ├── context/         # Context-related components
│   │   └── chat/            # Chat interface components
│   ├── features/             # Feature-based modules
│   │   ├── auth/            # Authentication
│   │   ├── projects/        # Project management
│   │   └── workspace/       # Workspace features
│   ├── hooks/                # Custom React hooks
│   ├── pages/                # Application pages/routes
│   ├── services/             # Frontend services
│   ├── store/                # State management (Redux/Zustand)
│   ├── styles/               # CSS and styling files
│   ├── types/                # TypeScript type definitions
│   └── utils/                # Frontend utility functions
├── tests/                     # Test suite
│   ├── backend/              # Backend tests
│   │   ├── unit/            # Unit tests
│   │   ├── integration/     # Integration tests
│   │   ├── performance/     # Performance tests
│   │   └── fixtures/        # Test fixtures
│   ├── frontend/             # Frontend tests
│   │   ├── unit/           # Component unit tests
│   │   ├── integration/    # Integration tests
│   │   └── visual/         # Visual regression tests
│   └── contracts/            # API contract tests
├── .env.sample               # Environment variables example
├── .gitignore               # Git ignore configuration
├── CLAUDE.md                # Claude AI instructions
├── docker-compose.yml       # Docker Compose configuration
├── GEMINI.md                # Gemini AI instructions
├── Makefile                 # Build automation
├── package.json             # Frontend dependencies
├── pyproject.toml           # Python project configuration
├── README.md                # Project description (this file)
└── requirements.txt         # Python dependencies
```

### Directory Descriptions

#### Backend (Python/FastAPI)
- **`app/`**: Main backend application directory
  - **`agents/`**: Multi-agent system implementation with specialized AI agents
  - **`analytics/`**: Usage analytics, metrics collection, and reporting
  - **`api/`**: RESTful API endpoints, WebSocket handlers, and middleware
  - **`core/`**: Core functionality including config, security, database, and logging
  - **`integrations/`**: External service integrations (AI providers, GitHub, VSCode)
  - **`models/`**: Data models (ORM, domain models, Pydantic schemas)
  - **`processing/`**: Document processing pipeline (parsing, chunking, embedding)
  - **`repositories/`**: Data access layer with repository pattern
  - **`services/`**: Business logic including agent coordination and context management
  - **`storage/`**: Storage interfaces for vector DBs, object storage, and caching
  - **`utils/`**: Shared utilities and helper functions

#### Frontend (React/TypeScript)
- **`src/`**: Main frontend application
  - **`api/`**: API client and data fetching logic
  - **`components/`**: Reusable UI components organized by function
  - **`features/`**: Feature-based modules following vertical slice architecture
  - **`hooks/`**: Custom React hooks for shared logic
  - **`pages/`**: Route-based page components
  - **`services/`**: Frontend services for business logic
  - **`store/`**: Global state management
  - **`types/`**: TypeScript type definitions and interfaces
  - **`utils/`**: Frontend utility functions

#### Infrastructure & Deployment
- **`docker/`**: Docker configurations for all services
- **`infrastructure/`**: Infrastructure as Code
  - **`kubernetes/`**: K8s manifests with Kustomize overlays
  - **`terraform/`**: Cloud infrastructure provisioning
  - **`helm/`**: Helm charts for Kubernetes deployment
- **`scripts/`**: Automation scripts for various tasks

#### Testing
- **`tests/`**: Comprehensive test suite
  - **`backend/`**: Unit, integration, and performance tests
  - **`frontend/`**: Component, integration, and visual tests
  - **`contracts/`**: API contract testing
- **`e2e/`**: End-to-end testing with Cypress and Playwright

#### Configuration & Documentation
- **`.github/`**: GitHub Actions workflows and templates
- **`ai_docs/`**: AI-generated documentation and task specifications
- **`docs/`**: Project documentation including API docs and architecture diagrams

This structure supports a scalable, microservices-ready architecture with:
- Clear separation of concerns
- Multi-agent AI system integration
- Comprehensive testing strategy
- Production-ready deployment configurations
- Extensive monitoring and analytics capabilities
