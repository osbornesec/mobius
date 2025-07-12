-- Mobius Context Engine - Database Initialization
-- This script sets up the initial database extensions for Phase 1
-- 
-- NOTE: Table definitions are now managed by Alembic migrations
-- This file only handles extensions and initial setup that cannot be managed by Alembic

-- Enable the pgvector extension (required for vector similarity search)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation (required for UUID primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- DEPRECATED: The following table definitions are now managed by Alembic
-- To create/update database schema, run: alembic upgrade head
-- 
-- The schema includes:
-- - projects: Project organization with UUID primary keys
-- - documents: File metadata with foreign key to projects
-- - embeddings: Vector embeddings with foreign key to documents
-- 
-- All tables use UUID primary keys and proper foreign key relationships
-- as defined in the SQLAlchemy models and Alembic migrations.

-- Optional: Script to run Alembic migrations during container startup
-- This could be added to a startup script:
-- alembic upgrade head
