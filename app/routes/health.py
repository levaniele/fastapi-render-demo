"""
Health check endpoint for monitoring service status.
Checks database, backend, and observability service connectivity.
"""

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db_session
from app.core.config import get_settings
from app.core.cache import get_cache_stats, clear_all_caches, invalidate_by_pattern
from app.core.dependencies import require_role

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check(db: Session = Depends(get_db_session)):
    """
    Comprehensive health check for all services.
    
    Returns:
        - backend: API server status
        - database: PostgreSQL connection status
        - observability: Go observability service status
        - timestamp: Current UTC time
    """
    health_status = {
        "backend": "unknown",
        "database": "unknown",
        "observability": "unknown",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "details": {}
    }
    
    # 1. Backend is OK if we got here
    health_status["backend"] = "ok"
    
    # 2. Check Database
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = "error"
        health_status["details"]["database_error"] = str(e)
    
    # 3. Check Observability Service
    if settings.observability_enabled:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # Try to reach the Go service health endpoint or events endpoint
                response = await client.get(f"{settings.observability_url}/health")
                if response.status_code == 200:
                    health_status["observability"] = "ok"
                else:
                    health_status["observability"] = "degraded"
                    health_status["details"]["observability_status"] = response.status_code
        except httpx.ConnectError:
            health_status["observability"] = "unavailable"
            health_status["details"]["observability_error"] = "Connection refused"
        except httpx.TimeoutException:
            health_status["observability"] = "timeout"
            health_status["details"]["observability_error"] = "Request timeout"
        except Exception as e:
            health_status["observability"] = "error"
            health_status["details"]["observability_error"] = str(e)
    else:
        health_status["observability"] = "disabled"
    
    # Determine overall status
    if all(v == "ok" for k, v in health_status.items() if k in ["backend", "database"]):
        if health_status["observability"] in ["ok", "disabled"]:
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"  # Observability down but core services OK
    else:
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/health/simple")
def simple_health():
    """Simple health check that just returns OK if the server is running."""
    return {"status": "ok"}


@router.get("/health/cache")
def cache_health():
    """
    Get cache statistics and health information.

    Returns:
        - Cache hit/miss statistics
        - Total cached keys
        - Hit rate percentage
        - Cache details by category
    """
    stats = get_cache_stats()

    # Add cache health status
    cache_enabled = settings.cache_enabled
    hit_rate = stats.get("hit_rate", 0)

    # Determine cache health
    if not cache_enabled:
        status = "disabled"
    elif hit_rate >= 80:
        status = "healthy"
    elif hit_rate >= 50:
        status = "degraded"
    else:
        status = "poor"

    return {
        "status": status,
        "enabled": cache_enabled,
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/health/cache/clear")
def clear_cache(current_user: dict = Depends(require_role("admin"))):
    """
    Clear all caches.

    WARNING: This will invalidate all cached data and may temporarily increase
    database load until caches are repopulated.

    Use this endpoint for:
    - Emergency cache clearing
    - After major data migrations
    - Debugging cache issues
    """
    try:
        clear_all_caches()
        return {
            "status": "success",
            "message": "All caches cleared successfully",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear caches: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@router.post("/health/cache/clear/{pattern}")
def clear_cache_by_pattern(
    pattern: str, current_user: dict = Depends(require_role("admin"))
):
    """
    Clear caches matching a specific pattern.

    Args:
        pattern: Pattern to match in cache keys (e.g., "tournament", "player", "rankings")

    Examples:
        - POST /health/cache/clear/tournament - Clears all tournament-related caches
        - POST /health/cache/clear/get_all_players - Clears player list cache
        - POST /health/cache/clear/summer-open-2024 - Clears specific tournament cache
    """
    try:
        count = invalidate_by_pattern(pattern)
        return {
            "status": "success",
            "message": f"Cleared {count} cache entries matching pattern '{pattern}'",
            "pattern": pattern,
            "cleared_count": count,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear cache pattern: {str(e)}",
            "pattern": pattern,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
