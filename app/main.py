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
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import get_settings
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
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",  # TODO: Get from settings when VERSION is added
        description="Context Engineering Platform for AI Coding Assistants",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        lifespan=lifespan,
    )
    
    # Add TrustedHostMiddleware for production security
    # This should be the first middleware to prevent host header attacks
    if settings.is_production():
        # In production, restrict to specific allowed hosts
        allowed_hosts = ["*.mobius.ai", "mobius.ai", "localhost"]
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
    else:
        # In development, allow common local hosts
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*.localhost"]
        )
    
    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
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
    # TODO: Add SENTRY_DSN to settings when configured
    # if settings.sentry_dsn:
    #     app.add_middleware(SentryAsgiMiddleware)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
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
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": "0.1.0",  # TODO: Get from settings when VERSION is added
        "description": "Context Engineering Platform for AI Coding Assistants",
        "docs": "/api/v1/docs",
        "health": "/api/v1/health",
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
    
    settings = get_settings()
    
    # Log security warning if binding to all interfaces
    if settings.host == "0.0.0.0":
        logger.warning(
            "Application is binding to 0.0.0.0 (all interfaces). "
            "Ensure proper firewall rules are in place."
        )
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )