# Mobius

**GitHub Repository:** [https://github.com/osbornesec/mobius](https://github.com/osbornesec/mobius)

## Overview

Mobius is a cutting-edge Context Engineering Platform designed for AI coding assistants. Built with FastAPI (Python) for the backend and React (TypeScript) for the frontend, Mobius provides intelligent context management, multi-agent coordination, and seamless IDE integration to enhance developer productivity.

### Key Features

- **Multi-Agent AI System**: Specialized AI agents for context building, retrieval, code generation, and orchestration
- **Intelligent Context Management**: Advanced context aggregation and relevance scoring for improved AI interactions
- **IDE Integration**: Language Server Protocol (LSP) implementation for VSCode and Cursor
- **Vector-Powered Search**: Integration with Qdrant and Pinecone for semantic code search and retrieval
- **Real-time Collaboration**: WebSocket-based real-time features for team collaboration
- **Enterprise Security**: OAuth2+JWT authentication, rate limiting, and comprehensive audit logging
- **Scalable Architecture**: Kubernetes-ready with multi-region deployment capabilities
- **Comprehensive Analytics**: Built-in metrics collection, performance monitoring, and usage analytics

### Technology Stack

- **Backend**: FastAPI, Python 3.11+, Pydantic, SQLAlchemy
- **Frontend**: React 18, TypeScript, Redux/Zustand, Vite
- **Databases**: PostgreSQL with pgvector, Redis for caching
- **Vector Storage**: Qdrant (primary), Pinecone (secondary)
- **Infrastructure**: Docker, Kubernetes, Terraform
- **AI Integrations**: OpenAI, Anthropic Claude, custom model adapters

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

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm/yarn
- **Docker** and Docker Compose
- **PostgreSQL 14+**
- **Redis 6+**

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/osbornesec/mobius.git
   cd mobius
   ```

2. **Set up environment variables**
   ```bash
   cp .env.sample .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose** (Recommended)
   ```bash
   docker-compose up -d
   ```

4. **Or run locally**
   ```bash
   # Backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload

   # Frontend (in another terminal)
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Installation

### Development Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
npm install

# Set up pre-commit hooks
# This will install the git hooks that run on every commit.
# See .pre-commit-config.yaml for the full list of hooks.
pre-commit install --install-hooks

# Run database migrations
alembic upgrade head

# Start development servers
make dev
```

### Production Deployment

See [deployment documentation](docs/deployment/) for detailed production setup instructions.

## Usage

### Basic API Usage

```python
import requests

# Example API call
response = requests.post("http://localhost:8000/api/v1/context/search", 
    json={"query": "authentication implementation"})
print(response.json())
```

### IDE Integration

Install the Mobius extension for VSCode or Cursor to enable intelligent context suggestions directly in your editor.

## API Documentation

- **OpenAPI/Swagger**: Available at `/docs` when running the server
- **ReDoc**: Available at `/redoc` for alternative API documentation
- **Detailed API Guide**: See [docs/api/](docs/api/)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Use ESLint and Prettier for TypeScript/React
- Write tests for new features
- Update documentation as needed

## Testing

```bash
# Run all tests
make test

# Backend tests only
pytest tests/backend/

# Frontend tests only
npm test

# E2E tests
npm run test:e2e
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/osbornesec/mobius/issues)
- **Discussions**: [GitHub Discussions](https://github.com/osbornesec/mobius/discussions)

## Roadmap

Mobius follows a comprehensive 24-month implementation plan spanning 4 phases. For detailed roadmap including timelines, budgets, and technical specifications, see our [Implementation Roadmap](ai_docs/IMPLEMENTATION_ROADMAP.md).

### Current Phase: Foundation (Months 1-3)
- [x] Project structure and documentation
- [ ] Core infrastructure setup (FastAPI, PostgreSQL, Redis)
- [ ] Basic context processing and vector embeddings
- [ ] Frontend foundation with React + TypeScript
- [ ] CI/CD pipeline and development environment

### Upcoming Phases:
- **Phase 2 (Months 4-8)**: MVP with AI integration and IDE support
- **Phase 3 (Months 9-16)**: Advanced multi-agent system and enterprise features  
- **Phase 4 (Months 17-24)**: Enterprise scale supporting 10k+ concurrent users

**Target Outcome**: Enterprise-grade AI context engineering platform with <200ms latency and multi-agent AI coordination.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://reactjs.org/)
- Vector storage powered by [Qdrant](https://qdrant.tech/)
- AI integrations with OpenAI and Anthropic Claude
