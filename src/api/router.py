"""
Main API router configuration.

This module provides the main API router that includes all versioned API routes.
"""

from fastapi import APIRouter

from .v1.router import api_router as v1_router

# Create main API router
main_router = APIRouter()

# Include versioned routers
main_router.include_router(v1_router, prefix="/v1")


# Health check endpoint at root level
@main_router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

# Root endpoint
@main_router.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Meditwin Agents API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

__all__ = ["main_router"]
