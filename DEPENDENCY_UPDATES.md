# Dependency Updates Documentation

## Overview

This document provides a comprehensive guide to the dependency updates made to the Mobius Context Engineering Platform project. It serves as a record of changes, migration guide for developers, and roadmap for future major version upgrades.

## Summary of Updates

### Backend Dependencies (Python)

#### Major Updates

- **LangChain**: Updated to `0.3.26` from `0.2.x`
- **Pinecone Client**: Updated to `6.0.0` from `5.x`
- **LangChain Community**: Updated to `0.3.14` from `0.2.x`
- **FastAPI**: Updated to `0.116.0` (latest stable)
- **SQLAlchemy**: Updated to `2.0.41` (latest in v2.x series)
- **Pydantic**: Updated to `2.11.7` (staying in v2.x)

#### Minor/Patch Updates

- **OpenAI**: Updated to `1.93.1`
- **Anthropic**: Updated to `0.57.1`
- **Scikit-learn**: Updated to `1.6.1`
- **Pandas**: Updated to `2.2.4`
- **NumPy**: Updated to `1.26.4` (staying in v1.x)
- **Celery**: Updated to `5.5.3`
- **Redis**: Updated to `6.2.0` (staying in v6.x)
- **Pytest**: Updated to `8.4.1`
- **Black**: Updated to `25.1.0`
- **Ruff**: Updated to `0.12.2`
- **MyPy**: Updated to `1.16.1`

### Frontend Dependencies (React/TypeScript)

#### Major Updates

- **React**: Staying at `18.3.1` (avoided React 19 for stability)
- **React Router DOM**: Updated to `6.28.0`
- **TypeScript**: Updated to `5.7.2`
- **Vite**: Updated to `6.0.3`
- **Axios**: Updated to `1.7.9`

#### UI Library Updates

- **Radix UI**: Updated all components to latest versions
- **TailwindCSS**: Updated to `3.4.15`
- **Lucide React**: Updated to `0.468.0`
- **Framer Motion**: Updated to `11.12.0`

#### Development Tool Updates

- **ESLint**: Updated to `9.17.0`
- **Prettier**: Updated to `3.4.2`
- **Vitest**: Updated to `2.1.8`
- **Storybook**: Updated to `8.4.7`

## Breaking Changes to Watch Out For

### 1. LangChain 0.3.x Breaking Changes

#### Critical Changes

- **Pydantic v1 to v2 Migration**: All `langchain_core.pydantic_v1` imports must be replaced with direct `pydantic` imports
- **Agent Classes Deprecated**: Most agent classes are deprecated in favor of new constructor methods
- **Import Reorganization**: Many modules moved to `langchain-community` package

#### Required Code Changes

```python
# BEFORE (will break)
from langchain_core.pydantic_v1 import BaseModel, validator

# AFTER (required)
from pydantic import BaseModel, field_validator
```

```python
# BEFORE (deprecated)
from langchain.agents import Agent, ZeroShotAgent

# AFTER (recommended)
from langgraph.prebuilt import create_react_agent
```

#### Migration Steps

1. Run the LangChain CLI migration tool:
   ```bash
   pip install -U langchain-cli
   langchain-cli migrate --diff [path to code]  # Preview changes
   langchain-cli migrate [path to code]  # Apply changes
   ```

2. Update Pydantic validators:
   ```python
   # BEFORE
   @validator('field_name')
   @classmethod
   def validate_field(cls, v):
       return v
   
   # AFTER
   @field_validator('field_name')
   @classmethod
   def validate_field(cls, v):
       return v
   ```

3. Call `model_rebuild()` on custom model classes after updating imports

### 2. Pinecone v6 Breaking Changes

#### Major API Changes

- **New Enum-Based Configuration**: Recommended to use enums instead of strings
- **Index Creation API Changes**: Updated method signatures
- **Async Support**: New `PineconeAsyncio` and `IndexAsyncio` classes

#### Required Code Changes

```python
# BEFORE (still works but deprecated)
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone()
pc.create_index(
    name='my-index',
    dimension=1536,
    metric='cosine',
    spec=ServerlessSpec(cloud='aws', region='us-west-2')
)

# AFTER (recommended)
from pinecone import (
    Pinecone,
    ServerlessSpec,
    CloudProvider,
    AwsRegion,
    Metric,
    VectorType
)

pc = Pinecone()
pc.create_index(
    name='my-index',
    dimension=1536,
    metric=Metric.COSINE,
    spec=ServerlessSpec(
        cloud=CloudProvider.AWS,
        region=AwsRegion.US_WEST_2
    ),
    vector_type=VectorType.DENSE
)
```

#### New Features to Leverage

1. **Backup and Restore**: New backup functionality for serverless indexes
2. **Sparse Vector Support**: Better support for sparse vectors
3. **Improved Error Handling**: Better error messages and recovery options

### 3. React 18.3.1 Considerations

#### Why We Stayed on React 18

- **Stability**: React 19 introduces significant breaking changes
- **Ecosystem Compatibility**: Many libraries not yet React 19 compatible
- **Migration Complexity**: Would require extensive testing and updates

#### React 18 Features We Can Leverage

1. **Automatic Batching**: Already enabled with our `createRoot` usage
2. **Concurrent Features**: `useTransition` and `useDeferredValue` available
3. **Suspense Improvements**: Better SSR support when we implement it

## Migration Notes for Developers

### Quick Start for New Developers

Getting started with the Mobius platform is straightforward:

1. **Clone the repository and set up environment**:
   ```bash
   git clone <repository-url>
   cd Mobius
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the development environment**:
   ```bash
   make dev
   ```

4. **Access the applications**:
   - Backend API: http://localhost:8000
   - Frontend UI: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

5. **Verify setup**:
   - Check that both services are running without errors
   - The frontend should connect to the backend automatically
   - Test a simple API endpoint in the Swagger UI at `/docs`

**Tips for new developers**:
- The `make dev` command handles all dependency installation and service startup
- Hot-reload is enabled for both frontend and backend during development
- Check the logs if either service fails to start - common issues are port conflicts or missing environment variables
- See the detailed setup instructions below for manual setup or troubleshooting

### Setting Up Development Environment

1. **Python Environment**:
   ```bash
   # Ensure Python 3.11+ is installed
   python --version  # Should be 3.11 or higher
   
   # Install updated dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Node.js Environment**:
   ```bash
   # Ensure Node.js 20+ is installed
   node --version  # Should be 20.0.0 or higher
   
   # Install frontend dependencies
   cd frontend
   npm install
   ```

### Code Migration Checklist

#### Backend Migration

- [ ] Run LangChain migration tool
- [ ] Update all Pydantic v1 imports to v2
- [ ] Replace deprecated agent classes with LangGraph equivalents
- [ ] Update Pinecone client initialization code
- [ ] Test all vector operations with new Pinecone client
- [ ] Verify FastAPI compatibility with updated dependencies
- [ ] Run full test suite to catch breaking changes

#### Frontend Migration

- [ ] Update any React component patterns that might be deprecated
- [ ] Test all TypeScript types with new version
- [ ] Verify Vite build configuration works with v6
- [ ] Test all UI components with updated Radix UI versions
- [ ] Ensure ESLint configuration works with v9
- [ ] Run full test suite including Storybook tests

### Common Issues and Solutions

#### 1. LangChain Import Errors

**Problem**: `ImportError: cannot import name 'BaseModel' from 'langchain_core.pydantic_v1'`

**Solution**: 
```python
# Replace this
from langchain_core.pydantic_v1 import BaseModel

# With this
from pydantic import BaseModel
```

#### 2. Pinecone Connection Issues

**Problem**: `AttributeError: 'Pinecone' object has no attribute 'Index'`

**Solution**: Update to new index access pattern:
```python
# Old pattern
index = pc.Index("index-name")

# New pattern
desc = pc.describe_index("index-name")
index = pc.Index(host=desc.host)
```

#### 3. React TypeScript Errors

**Problem**: Type errors with updated React types

**Solution**: Run the React 19 codemod even though we're on React 18:
```bash
npx types-react-codemod@latest preset-19 ./frontend/src
```

## Testing Recommendations

### 1. Comprehensive Test Plan

#### Backend Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires API keys)
pytest tests/integration/ -v

# LangChain specific tests
pytest tests/unit/test_langchain_integration.py -v

# Pinecone specific tests
pytest tests/unit/test_vector_store.py -v

# Full test suite
pytest tests/ --cov=app --cov=mobius
```

#### Frontend Testing

```bash
cd frontend

# Unit tests
npm run test

# Type checking
npm run typecheck

# Build test
npm run build

# Storybook tests
npm run test-storybook

# E2E tests (if implemented)
npm run test:e2e
```

### 2. Manual Testing Checklist

#### Core Functionality

- [ ] **Context Processing Pipeline**: Test with various input types
- [ ] **Vector Operations**: Test upsert, query, and delete operations
- [ ] **LLM Integrations**: Test OpenAI and Anthropic API calls
- [ ] **Multi-Agent System**: Test agent coordination and communication
- [ ] **Memory Systems**: Test context storage and retrieval
- [ ] **API Endpoints**: Test all FastAPI routes
- [ ] **Authentication**: Test OAuth2/JWT flow
- [ ] **Real-time Features**: Test WebSocket connections

#### UI Components

- [ ] **Context Builder Interface**: Test all input methods
- [ ] **Retrieval Interface**: Test search and filtering
- [ ] **Agent Dashboard**: Test agent status and coordination
- [ ] **Settings Pages**: Test all configuration options
- [ ] **Real-time Updates**: Test live data synchronization

### 3. Performance Testing

```bash
# Backend performance
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Frontend performance
npm run analyze  # Bundle size analysis

# Memory profiling
python -m memory_profiler scripts/profile_memory.py
```

## Future Upgrade Path

### Immediate Next Steps (Next 3-6 Months)

1. **React 19 Migration**
   - **Timeline**: Q2 2025
   - **Prerequisites**: Wait for ecosystem compatibility
   - **Key Changes**: New React Compiler, Server Components, Actions
   - **Preparation**: Start using React 18 patterns that are React 19 compatible

2. **Python 3.12+ Migration**
   - **Timeline**: Q1 2025
   - **Benefits**: Better performance, new syntax features
   - **Prerequisites**: Ensure all dependencies support Python 3.12

### Medium-term Upgrades (6-12 Months)

1. **LangChain 0.4+ (when available)**
   - Monitor for LangChain v0.4 release
   - Evaluate new features and breaking changes
   - Plan migration strategy

2. **FastAPI 1.0+**
   - Monitor FastAPI roadmap for v1.0 release
   - Evaluate breaking changes and new features
   - Plan migration timeline

3. **Pinecone v7+ (when available)**
   - Monitor for new features and improvements
   - Evaluate impact on our vector operations
   - Plan gradual migration

### Long-term Considerations (12+ Months)

1. **NumPy 2.0+ Migration**
   - Currently staying on v1.x for compatibility
   - Plan migration when ecosystem fully supports v2.0
   - Test extensively due to potential breaking changes

2. **Redis 7.x+ Migration**
   - Evaluate new features in Redis 7.x
   - Plan migration for improved performance
   - Test clustering and persistence features

3. **Next-generation AI Libraries**
   - Monitor for LangGraph v1.0 stable release
   - Evaluate new AI orchestration frameworks
   - Consider migration to more advanced agent frameworks

## Monitoring and Maintenance

### 1. Dependency Monitoring

Set up automated dependency monitoring:

```bash
# Add to CI/CD pipeline
pip-audit  # Security vulnerability scanning
safety check  # Python package security
npm audit  # Node.js package security
```

### 2. Regular Update Schedule

- **Security Updates**: Apply immediately upon release
- **Patch Updates**: Monthly review and application
- **Minor Updates**: Quarterly evaluation and planning
- **Major Updates**: Bi-annual planning and implementation

### 3. Breaking Change Alerts

Set up monitoring for:
- LangChain release notes and migration guides
- Pinecone client library changes
- React and TypeScript breaking changes
- FastAPI and Pydantic updates
- Critical security advisories

## Conclusion

This dependency update significantly modernizes the Mobius platform while maintaining stability. The careful approach of avoiding major breaking changes (like React 19) while updating to the latest stable versions provides a solid foundation for continued development.

Key success factors for this update:
1. **Thorough Testing**: Comprehensive test coverage catches regressions
2. **Gradual Migration**: Phased approach reduces risk
3. **Documentation**: Clear migration guides help team adoption
4. **Monitoring**: Ongoing dependency tracking prevents security issues

The platform is now positioned for continued development with modern, secure, and performant dependencies while maintaining a clear path for future major version upgrades.