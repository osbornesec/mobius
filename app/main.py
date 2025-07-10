"""
Mobius Context Engineering Platform - Main FastAPI Application

This module initializes and configures the FastAPI application with all
necessary middleware, routes, and event handlers.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging import logger, LogConfig
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.logging import LoggingMiddleware
from app.models.database import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    
    Handles startup and shutdown operations for the FastAPI application.
    """
    # Startup
    logger.info("Starting Mobius Context Engineering Platform...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize vector stores
    # TODO: Initialize Qdrant and Pinecone connections
    
    # Initialize cache
    # TODO: Initialize Redis connection
    
    logger.info("Mobius platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mobius platform...")
    
    # Close database connections
    await engine.dispose()
    
    # Close vector store connections
    # TODO: Close Qdrant and Pinecone connections
    
    # Close cache connections
    # TODO: Close Redis connection
    
    logger.info("Mobius platform shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Context Engineering Platform for AI Coding Assistants",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )
    
    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add correlation ID handling (must be first to set correlation ID)
    log_config = LogConfig()
    app.add_middleware(
        CorrelationIdMiddleware,
        header_name=log_config.correlation_id_header,
        generate_id_if_missing=True
    )
    
    # Add request/response logging (after correlation ID middleware)
    app.add_middleware(LoggingMiddleware, log_config=log_config)
    
    # Add Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add Sentry error tracking
    if settings.SENTRY_DSN:
        app.add_middleware(SentryAsgiMiddleware)
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add Prometheus metrics
    Instrumentator().instrument(app).expose(app)
    
    return app


# Create the FastAPI app instance
app = create_application()


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Dict[str, Any]: API information
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Context Engineering Platform for AI Coding Assistants",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring.
    
    Returns:
        Dict[str, str]: Health status
    """
    # TODO: Add actual health checks for database, cache, and vector stores
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )