# Mobius Context Engine - Quick Start Guide

This guide will get you up and running with the Mobius Context Engineering Platform in under 10 minutes.

## Prerequisites

Ensure you have the following installed:
- Docker and Docker Compose
- Git
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

## Phase 1 Setup (Current)

### 1. Clone and Setup the Environment

```bash
# Navigate to project directory (already done)
cd /home/michael/dev/Mobius

# Create environment file
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://mobius:mobius@localhost:5432/mobius
POSTGRES_DB=mobius
POSTGRES_USER=mobius
POSTGRES_PASSWORD=mobius

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=your_secret_key_here_change_in_production
EOF
```

### 2. Start the Infrastructure

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check that all services are running
docker-compose ps

# View logs if needed
docker-compose logs -f backend
```

### 3. Verify the Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs

# Check Qdrant dashboard
open http://localhost:6333/dashboard
```

Expected response from health check:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

### 4. Test Basic Functionality

```bash
# Test file ingestion
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/test/example.py",
    "content": "def hello_world():\n    print(\"Hello, World!\")",
    "file_type": "python"
  }'

# Test search functionality
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hello world function",
    "limit": 5
  }'

# Check platform statistics
curl http://localhost:8000/stats
```

## Development Setup

### Backend Development

```bash
# Create Python virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend locally (optional - can use Docker)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development (Phase 2)

```bash
# Create React application
cd frontend
npx create-react-app . --template typescript
npm install zustand axios react-router-dom @types/react-router-dom

# Start development server
npm start
```

## Database Management

### Connect to PostgreSQL

```bash
# Connect to database
docker exec -it mobius-postgres psql -U mobius -d mobius

# View tables
\dt

# Check embeddings table
SELECT COUNT(*) FROM embeddings;

# Exit
\q
```

### Qdrant Management

```bash
# Check collections
curl http://localhost:6333/collections

# Create a test collection
curl -X PUT "http://localhost:6333/collections/test" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

## Next Steps

Once you have the basic setup running, proceed with these development tasks:

### Week 1-2 Tasks
1. **Implement Embedding Generation**
   - Add OpenAI API integration
   - Create embedding service
   - Test with sample files

2. **Complete Database Integration**
   - Implement SQLAlchemy models
   - Add database operations
   - Create migration system

3. **Build Basic Search**
   - Vector similarity search
   - Result ranking
   - Performance optimization

### Week 3-4 Tasks
1. **Frontend Development**
   - Create React components
   - Implement search interface
   - Add file upload functionality

2. **API Enhancement**
   - Add authentication
   - Implement rate limiting
   - Add error handling

3. **Testing Framework**
   - Unit tests for backend
   - Integration tests
   - Performance benchmarks

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check if PostgreSQL is running
   docker-compose logs postgres

   # Restart if needed
   docker-compose restart postgres
   ```

2. **Port Conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :8000  # Backend
   lsof -i :5432  # PostgreSQL
   lsof -i :6379  # Redis
   lsof -i :6333  # Qdrant
   ```

3. **Docker Issues**
   ```bash
   # Clean up Docker resources
   docker-compose down -v
   docker system prune -f
   docker-compose up -d --build
   ```

### Getting Help

- Check the logs: `docker-compose logs <service_name>`
- Review the API docs: http://localhost:8000/docs
- Consult the implementation roadmap: `IMPLEMENTATION_ROADMAP.md`

## Success Criteria

You've successfully completed the Phase 1 setup when:

- [ ] All Docker services are running
- [ ] Backend API responds to health checks
- [ ] Database tables are created with proper indexes
- [ ] Basic ingestion endpoint accepts files
- [ ] Search endpoint returns mock results
- [ ] API documentation is accessible

## Phase 2 Preparation

To prepare for Phase 2 development:

1. Set up your OpenAI API key in the `.env` file
2. Familiarize yourself with the FastAPI documentation
3. Review the PostgreSQL pgvector documentation
4. Study the Qdrant client documentation
5. Plan your first real file ingestion workflow

This foundation will support all future development phases as outlined in the implementation roadmap.
