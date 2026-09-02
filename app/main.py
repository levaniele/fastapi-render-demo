"""
Main FastAPI application for Badminton 360 API.
Handles CORS, router registration, and server configuration.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core import system_metrics
from app.core.middleware import TraceMiddleware

# Adjust import since we are in app/ using absolute imports from root (assuming root is in pythonpath)
# or relative imports. Since this is the app package, absolute imports usually work if running from root.
from app.core.config import get_settings
from app.core.cache import initialize_caches
from app.database import engine
from app.routes import (
    auth,
    dashboard,
    clubs,
    players,
    tournaments,
    coaches,
    officials,
    rankings,
    matches,
    health,
)

# 1. Load Settings
settings = get_settings()
logger = logging.getLogger(__name__)

# 2. Define App Metadata
docs_enabled = settings.docs_enabled and (
    not settings.is_production or settings.docs_in_production
)

app = FastAPI(
    title="Badminton360 API",
    description="API for Badminton360. Official GNBF Registry API.",
    version="1.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

# 4. CORS Middleware
allowed_origins = settings.parsed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Trace-Id",
        "X-Span-Id",
        "X-Parent-Span-Id",
    ],
)

# Add Trace Middleware
app.add_middleware(TraceMiddleware)

# 5. Router Registration
app.include_router(health.router)  # Health checks first
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tournaments.router)
app.include_router(players.router)
app.include_router(clubs.router)
app.include_router(coaches.router)
app.include_router(officials.router)
app.include_router(matches.router)
app.include_router(rankings.router)

# 6. Event Handlers
@app.on_event("startup")
def _startup() -> None:
    """Initialize caches on application startup."""
    try:
        initialize_caches(settings)
        logger.info("Cache system initialized successfully")
    except Exception as err:
        logger.error(f"Failed to initialize cache system: {err}")


@app.on_event("shutdown")
def _shutdown() -> None:
    """Dispose SQLAlchemy engine on shutdown to close pooled connections."""
    try:
        engine.dispose()
    except (RuntimeError, OSError) as e:
        # Only catch specific exceptions related to engine disposal
        logger.error(f"Error disposing database engine on shutdown: {e}")
    finally:
        try:
            system_metrics.system_metrics_recorder.stop()
        except Exception as err:
            logger.debug("Stopping system metrics recorder failed: %s", err)

# 7. Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    Returns API status and version information.
    """
    return {
        "message": "Badminton 360 API is Online",
        "version": "1.0.0",
        "status": "operational",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=not settings.is_production, 
        log_level=settings.log_level.lower()
    )
