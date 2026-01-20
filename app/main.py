"""
Main FastAPI application for Badminton 360 API.
Handles CORS, router registration, and server configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

from app.database import get_db
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

app = FastAPI(
    title="Badminton 360 API", description="Official GNBF Registry API", version="1.0.0"
)

# ============================================================================
# ADD CORS MIDDLEWARE (Place RIGHT AFTER app = FastAPI())
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:3001",  # Backup port
    ],
    allow_credentials=True,  # IMPORTANT: Allow cookies
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================
app.include_router(auth.router)
app.include_router(tournaments.router)
app.include_router(players.router)
app.include_router(clubs.router)
app.include_router(coaches.router)
app.include_router(officials.router)
app.include_router(matches.router)
app.include_router(rankings.router)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================
@app.get("/", tags=["Root"])
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
    return {"ok": True, "service": "badminton360"}


@app.get("/db/health", tags=["Health"])
def db_health():
    try:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                value = cur.fetchone()[0]
            return {"ok": True, "db": "connected", "select_1": value}
        finally:
            conn.close()
    except psycopg2.OperationalError:
        return {"ok": False, "db": "error"}
    except Exception as e:
        return {"ok": False, "db": "error", "error": str(e)}


# ============================================================================
# SERVER STARTUP
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
