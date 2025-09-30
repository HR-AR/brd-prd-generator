"""
Main FastAPI application for BRD/PRD Generator.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from dotenv import load_dotenv

from src.api.endpoints import router
from src.core.exceptions import BRDPRDGeneratorError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Performs startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting BRD/PRD Generator API...")

    # Initialize any required resources
    # Could initialize database connections, caches, etc.

    yield

    # Shutdown
    logger.info("Shutting down BRD/PRD Generator API...")

    # Clean up resources
    # Could close database connections, flush caches, etc.


# Create FastAPI app
app = FastAPI(
    title="BRD/PRD Generator API",
    description="Automated Business and Product Requirements Document generation using multi-LLM support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files directory
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API router
app.include_router(router)


# Global exception handlers
@app.exception_handler(BRDPRDGeneratorError)
async def brd_prd_exception_handler(request: Request, exc: BRDPRDGeneratorError):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc),
            "path": str(request.url)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "detail": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "detail": exc.detail,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred",
            "path": str(request.url)
        }
    )


# Root endpoint - serve the HTML interface
@app.get("/")
async def root():
    """Serve the HTML interface for document generation."""
    html_file = Path(__file__).parent.parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(str(html_file))
    else:
        # Fallback to API info if HTML not found
        return {
            "name": "BRD/PRD Generator API",
            "version": "1.0.0",
            "status": "operational",
            "documentation": "/docs",
            "health": "/api/v1/health"
        }


# Metrics endpoint (basic)
@app.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint.

    In production, would integrate with Prometheus or similar.
    """
    return {
        "requests_total": 0,  # Would track actual requests
        "documents_generated": 0,  # Would track generations
        "average_generation_time_ms": 0,  # Would calculate average
        "active_connections": 0  # Would count WebSocket connections
    }


if __name__ == "__main__":
    # Run with uvicorn when executed directly
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )