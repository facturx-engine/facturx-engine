"""
Factur-X API - Main Application Entry Point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.diagnostics import router as diagnostics_router
from app.version import __version__

# Configure logging
import json
import sys

# Structured JSON Logging for Industrial Grade Observability
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        # Add extra context if present
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

# Configure Log Handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

logger = logging.getLogger(__name__)

import os

from app.constants import PRODUCT_NAME, PRODUCT_VERSION, COMMUNITY_EDITION_NAME, PRO_EDITION_NAME

# Create FastAPI application
app = FastAPI(
    title=PRODUCT_NAME,
    description="Production-ready REST API for Factur-X (ZUGFeRD 2.2) conversions and data extraction.",
    version=PRODUCT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Switch to on_event which is more robust for logging in some versions
@app.on_event("startup")
async def startup_event():
    # STARTUP: Validating Environment
    logger.info(f"Initializing {PRODUCT_NAME}...")
    
    # LICENSE CHECK: Fail Fast Strategy
    try:
        # Try to import licensing module (Only in Pro)
        from app.license import is_licensed
        
        license_key = os.getenv("LICENSE_KEY", "").strip()
        
        if license_key:
            # User explicitly requested Pro Mode
            logger.info("Verifying License Key integrity...")
            if not is_licensed():
                logger.critical("🚨 FATAL CONFIGURATION ERROR: The provided LICENSE_KEY is INVALID.")
                logger.critical("   The application is refusing to start to prevent accidental fallback to Demo Mode.")
                sys.exit(1) # Crash container immediately
            else:
                logger.info("✅ PRO LICENSE VERIFIED. Full Engine Capabilities Unlocked.")
        else:
            logger.warning("ℹ️ No LICENSE_KEY found. Engine running in LIMITED DEMO MODE.")
            
    except ImportError:
        # Community Edition
        logger.info("ℹ️ Factur-X Community Edition Active.")
    except Exception as e:
        logger.critical(f"CRITICAL STARTUP ERROR: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API...")

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# SECURITY: DoS Protection via Max Upload Size (20MB)
class LimitUploadSize(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int) -> None:
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        if request.method == 'POST':
            if 'content-length' in request.headers:
                try:
                    content_length = int(request.headers['content-length'])
                    if content_length > self.max_upload_size:
                        logger.warning(f"Blocked upload exceeding size limit: {content_length} bytes")
                        return Response("File too large. Max size is 20MB.", status_code=413)
                except ValueError:
                    pass # Invalid header, let it proceed or fail later
        return await call_next(request)

# Configure Middlewares
# 1. Size Limit (First line of defense)
app.add_middleware(LimitUploadSize, max_upload_size=20 * 1024 * 1024) # 20MB

# 2. Configure CORS (Secure by Default logic)
cors_env = os.getenv("CORS_ORIGINS", "*")
allow_origins = [origin.strip() for origin in cors_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(diagnostics_router)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Factur-X API",
        "version": __version__,
        "endpoints": {
            "extract": "/v1/extract",
            "convert": "/v1/convert",
            "validate": "/v1/validate",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "factur-x-api",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
