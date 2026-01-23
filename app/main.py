"""
Main FastAPI application for Badminton 360 API.
Handles CORS, router registration, and server configuration.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Adjust import since we are in app/ using absolute imports from root (assuming root is in pythonpath)
# or relative imports. Since this is the app package, absolute imports usually work if running from root.
from app.core.config import get_settings
from app.database import engine
from app.routes import (
    auth,
    clubs,
    players,
    tournaments,
    coaches,
    officials,
    rankings,
    matches,
)

# 1. Load Settings
settings = get_settings()

# 2. Configure Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("app")

# 3. Define App Metadata
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Router Registration
app.include_router(auth.router)
app.include_router(tournaments.router)
app.include_router(players.router)
app.include_router(clubs.router)
app.include_router(coaches.router)
app.include_router(officials.router)
app.include_router(matches.router)
app.include_router(rankings.router)

# 6. Event Handlers
@app.on_event("shutdown")
def _shutdown() -> None:
    """Dispose SQLAlchemy engine on shutdown to close pooled connections."""
    try:
        engine.dispose()
    except Exception:
        logger.exception("Error disposing database engine on shutdown")

# 7. Health Checks
@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint.
    Returns API status and version information.
    """
    return {
        "message": "Badminton 360 API is Online",
        "version": "1.0.0",
        "status": "operational",
    }

@app.get("/health", tags=["Health"])
def health():
    return {"ok": True, "service": "badminton360", "db": "not_checked"}

@app.get("/db/health", tags=["Health"])
def db_health():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;"))
            val = result.scalar()
        return {"ok": True, "db": "connected", "select_1": val}
    except Exception as e:
        logger.exception("DB health check failed")
        if settings.is_production:
            return {"ok": False, "db": "error"}
        return {"ok": False, "db": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=not settings.is_production, 
        log_level=settings.log_level.lower()
    )
