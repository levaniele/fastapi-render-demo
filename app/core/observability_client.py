"""
Observability client for sending logs to Go observability service.
Implements fire-and-forget HTTP logging with graceful degradation.
"""

import httpx
import logging
import time
import asyncio
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.core.trace_context import get_trace_context

logger = logging.getLogger(__name__)
settings = get_settings()
_obs_client: Optional[httpx.AsyncClient] = None
_missing_key_warned = False


@dataclass
class DbMetricsSnapshot:
    """Snapshot of database metrics for a time window."""
    query_count: int = 0
    select_count: int = 0
    insert_count: int = 0
    update_count: int = 0
    delete_count: int = 0
    error_count: int = 0
    avg_query_ms: float = 0.0
    max_query_ms: float = 0.0
    pool_size: int = 0
    pool_checked_out: int = 0


class DbMetricsCollector:
    """Collects database metrics for periodic reporting."""

    WINDOW_SECONDS = 30.0

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._query_times: deque[tuple[float, float, str]] = deque()  # (timestamp, duration_ms, query_type)
        self._error_count = 0
        self._engine: Optional[Engine] = None

    def set_engine(self, engine: Engine) -> None:
        """Set the SQLAlchemy engine for pool stats."""
        self._engine = engine

    def record_query(self, duration_ms: float, query_type: str) -> None:
        """Record a query execution."""
        now = time.monotonic()
        with self._lock:
            self._query_times.append((now, duration_ms, query_type))
            self._prune_old_entries(now)

    def record_error(self) -> None:
        """Record a database error."""
        with self._lock:
            self._error_count += 1

    def get_snapshot_and_reset(self) -> DbMetricsSnapshot:
        """Get current metrics and reset counters."""
        now = time.monotonic()
        with self._lock:
            self._prune_old_entries(now)

            snapshot = DbMetricsSnapshot()

            if self._query_times:
                durations = []
                for _, duration_ms, query_type in self._query_times:
                    durations.append(duration_ms)
                    snapshot.query_count += 1
                    if query_type == "select":
                        snapshot.select_count += 1
                    elif query_type == "insert":
                        snapshot.insert_count += 1
                    elif query_type == "update":
                        snapshot.update_count += 1
                    elif query_type == "delete":
                        snapshot.delete_count += 1

                if durations:
                    snapshot.avg_query_ms = sum(durations) / len(durations)
                    snapshot.max_query_ms = max(durations)

            snapshot.error_count = self._error_count

            # Get pool stats if engine is available
            if self._engine is not None:
                pool = self._engine.pool
                snapshot.pool_size = pool.size()
                snapshot.pool_checked_out = pool.checkedout()

            # Reset error counter
            self._error_count = 0

            return snapshot

    def _prune_old_entries(self, now: float) -> None:
        """Remove entries older than the window."""
        cutoff = now - self.WINDOW_SECONDS
        while self._query_times and self._query_times[0][0] < cutoff:
            self._query_times.popleft()


# Global collector instance
db_metrics_collector = DbMetricsCollector()


async def log_event(
    level: str,
    type: str,
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """
    Send a log event to the Go observability service.
    
    This is a fire-and-forget operation that won't block or fail the request.
    
    Args:
        level: Log level - "info", "warn", or "error"
        type: Event type - "http", "db", "auth", "event", etc.
        name: Event name - e.g., "http.request", "auth.login.success"
        attributes: Optional dictionary of event attributes
        status_code: Optional HTTP status code
        duration_ms: Optional duration in milliseconds
        
    Example:
        await log_event(
            level="info",
            type="auth",
            name="auth.login.success",
            attributes={"user_id": 123, "email": "user@example.com"}
        )
    """
    if not settings.observability_enabled:
        return

    global _missing_key_warned
    if not settings.obs_api_key:
        if not _missing_key_warned:
            logger.warning("Observability enabled but OBS_API_KEY is not set. Skipping event export.")
            _missing_key_warned = True
        return


    trace = get_trace_context()
    if not trace:
        logger.debug("No trace context available for observability logging")
        return

    # Build payload matching Go service contract
    # Use ISO 8601 UTC timestamp: "2026-01-29T13:00:00.000Z"
    now = datetime.utcnow()
    # Format: YYYY-MM-DDTHH:MM:SS.mmmZ
    ts_formatted = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    payload = {
        "v": 1,
        "ts": ts_formatted,
        "traceId": trace.trace_id,
        "spanId": trace.span_id,
        "service": {
            "name": "badminton_api",
            "env": "development" if settings.app_env == "local" else settings.app_env,
            "version": settings.version,
        },
        "sdkLanguage": "python",
        "sdkVersion": settings.version,
        "level": level,
        "type": type,
        "name": name,
        "attributes": attributes or {},
    }

    # Add optional fields
    if trace.parent_span_id:
        payload["parentSpanId"] = trace.parent_span_id
    if status_code is not None:
        payload["statusCode"] = status_code
    if duration_ms is not None:
        payload["durationMs"] = round(duration_ms, 2)

    try:
        # Debug: log the payload being sent
        logger.debug(f"Sending observability event: {payload}")
        
        # Fire-and-forget with short timeout
        headers = {
            "Content-Type": "application/json",
            "X-Obs-Sdk-Language": "python",
        }
        if settings.obs_api_key:
            headers["X-Obs-Api-Key"] = settings.obs_api_key

        global _obs_client
        if _obs_client is None or _obs_client.is_closed:
            _obs_client = httpx.AsyncClient(timeout=1.0)

        response = await _obs_client.post(
            f"{settings.observability_url}/observability/events",
            json=payload,
            headers=headers,
        )

        # Log if not successful
        if response.status_code != 200:
            logger.warning(
                f"Observability service returned {response.status_code}: {response.text}"
            )
    except httpx.TimeoutException:
        logger.debug("Observability service timeout (non-critical)")
    except httpx.ConnectError:
        logger.debug("Cannot connect to observability service (non-critical)")
    except Exception as e:
        # Don't let observability failures break the application
        logger.debug(f"Failed to send observability event: {e}")


def scrub_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive fields from attributes before logging.
    
    Args:
        data: Dictionary that may contain sensitive data
        
    Returns:
        Scrubbed dictionary safe for logging
    """
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "session",
    }

    scrubbed = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            scrubbed[key] = "[REDACTED]"
        elif isinstance(value, dict):
            scrubbed[key] = scrub_sensitive_data(value)
        else:
            scrubbed[key] = value

    return scrubbed


def _get_query_type(statement: str) -> str:
    """Extract query type from SQL statement."""
    statement = statement.strip().upper()
    if statement.startswith("SELECT"):
        return "select"
    elif statement.startswith("INSERT"):
        return "insert"
    elif statement.startswith("UPDATE"):
        return "update"
    elif statement.startswith("DELETE"):
        return "delete"
    else:
        return "other"


def setup_db_logging(engine: Engine) -> None:
    """
    Set up SQLAlchemy event listeners to log database operations.

    Call this after creating your SQLAlchemy engine to enable DB logging.

    Args:
        engine: SQLAlchemy Engine instance
    """
    # Set engine for pool stats
    db_metrics_collector.set_engine(engine)

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_time = conn.info["query_start_time"].pop()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        query_type = _get_query_type(statement)
        statement_preview = " ".join(statement.split())[:220]

        # Record to metrics collector
        db_metrics_collector.record_query(duration_ms, query_type)

        if settings.db_log_queries:
            if duration_ms >= settings.db_slow_query_ms:
                logger.warning(
                    "[db][slow] type=%s duration_ms=%.2f rows=%s sql=%s",
                    query_type,
                    duration_ms,
                    cursor.rowcount,
                    statement_preview,
                )
            else:
                logger.info(
                    "[db][query] type=%s duration_ms=%.2f rows=%s sql=%s",
                    query_type,
                    duration_ms,
                    cursor.rowcount,
                    statement_preview,
                )

        # Fire-and-forget: schedule the async log in the event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_event(
                level="info",
                type="db",
                name=f"db.query.{query_type}",
                attributes={
                    "query_type": query_type,
                    "statement": statement[:500] if len(statement) > 500 else statement,
                },
                duration_ms=duration_ms,
            ))
        except RuntimeError:
            # No running event loop, skip logging
            pass

    @event.listens_for(engine, "handle_error")
    def handle_error(exception_context):
        """Log database errors."""
        db_metrics_collector.record_error()
        logger.error(
            "[db][error] statement=%s error=%s",
            str(exception_context.statement)[:500] if exception_context.statement else None,
            str(exception_context.original_exception),
        )
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_event(
                level="error",
                type="db",
                name="db.error",
                attributes={
                    "error": str(exception_context.original_exception),
                    "statement": str(exception_context.statement)[:500] if exception_context.statement else None,
                },
            ))
        except RuntimeError:
            pass
