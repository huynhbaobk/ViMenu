from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import uvicorn
import os
from datetime import datetime

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlingMiddleware,
    FileValidationMiddleware
)
from app.core.exceptions import (
    vimenu_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    ViMenuException
)
from app.core.dependencies import get_cache_service, get_ingredient_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    setup_logging()
    
        # Initialize services for caching dependencies
    cache_service = get_cache_service()
    ingredient_service = get_ingredient_service()
    
    logger.info("ViMenu application started successfully")
    
    # Store services in app state for cleanup
    app.state.cache_service = cache_service
    
    yield
    
    # Shutdown
    if hasattr(app.state, 'cache_service'):
        await app.state.cache_service.close()


app = FastAPI(
    title="Vietnamese Menu Analyzer",
    description="AI-powered Vietnamese menu extraction and ingredient analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None
)

# Add middleware (order matters - first added is outermost)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(FileValidationMiddleware, max_file_size=settings.MAX_FILE_SIZE)
app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware - More permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# Add CORS middleware for production
if settings.is_production:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Exception handlers
app.add_exception_handler(ViMenuException, vimenu_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router)

# Serve static files
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check cache service
        cache_service = get_cache_service()
        cache_stats = await cache_service.get_stats()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "services": {
                "cache": cache_stats.get("status", "unknown"),
                "mock_mode": settings.USE_MOCK_SERVICES
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "error": str(e)
        }


@app.get("/metrics")
async def get_metrics():
    """Application metrics endpoint"""
    if not settings.is_development:
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        cache_service = get_cache_service()
        cache_stats = await cache_service.get_stats()
        
        return {
            "cache": cache_stats,
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.is_development
    )