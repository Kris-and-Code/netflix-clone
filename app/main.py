from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from datetime import datetime
from typing import Any

from .routes import auth, content, user
from .utils.db import connect_to_mongo, close_mongo_connection
from .config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Netflix Clone API",
    description="A modern API for a Netflix-like streaming service",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this based on your environment
)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request middleware for logging and timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = datetime.utcnow()
    try:
        response = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds()
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request details
        logger.info(
            f"Path: {request.url.path} | "
            f"Method: {request.method} | "
            f"Process Time: {process_time:.3f}s | "
            f"Status: {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# Custom error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "path": request.url.path
        }
    )

# Generic error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "path": request.url.path
        }
    )

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": app.version
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    try:
        await connect_to_mongo()
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    try:
        await close_mongo_connection()
        logger.info("Successfully closed MongoDB connection")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Include routers with prefix and tags
api_router_config = [
    (auth.router, "auth", "Authentication endpoints"),
    (content.router, "content", "Content management endpoints"),
    (user.router, "user", "User management endpoints"),
]

for router, prefix, tag_description in api_router_config:
    app.include_router(
        router,
        prefix=f"/api/{prefix}",
        tags=[{
            "name": prefix.capitalize(),
            "description": tag_description
        }]
    )

# Optional: Add API versioning
@app.get("/api/version")
async def get_version():
    return {
        "version": app.version,
        "environment": settings.environment,
        "api_status": "operational"
    }

# Optional: Add system metrics endpoint
@app.get("/api/metrics")
async def get_metrics():
    import psutil
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4,
        log_level="info"
    ) 