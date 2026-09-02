"""Simple in-process collector for system resource events sent via obs360."""

from __future__ import annotations

import logging
import os
import threading
import gc
import time
from collections import deque
from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.observability_client import db_metrics_collector
from app.core.cache import get_cache_stats

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - psutil might not be installed in test envs
    psutil = None  # type: ignore[assignment]


class SystemMetricsRecorder:
    """Collects CPU/memory metrics and ships them to the obs360 collector."""

    DEFAULT_INTERVAL_SECONDS = 30.0
    METRICS_PATH = "observability/metrics"
    REQUEST_WINDOW_SECONDS = 30.0

    def __init__(self, interval_seconds: float = DEFAULT_INTERVAL_SECONDS) -> None:
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._start_lock = threading.Lock()
        self._disabled_reason: Optional[str] = None
        self._process: Optional["psutil.Process"] = None
        self._metrics_url = self._build_url(settings.observability_url, self.METRICS_PATH)
        self._request_timestamps: deque[float] = deque()
        self._request_lock = threading.Lock()

        if not settings.observability_enabled:
            self._disabled_reason = "observability feature flag is disabled"
        elif os.getenv("VERCEL"):
            self._disabled_reason = "background metrics are disabled on Vercel"
        elif not self._metrics_url:
            self._disabled_reason = "observability URL is not configured"
        elif psutil is None:
            self._disabled_reason = "psutil package is not installed"
        else:
            try:
                self._process = psutil.Process(os.getpid())
                psutil.cpu_percent(interval=None)
            except Exception as err:  # psutil.Error is not defined when psutil is None
                self._disabled_reason = f"failed to prepare psutil.Process: {err}"

        self._headers = self._build_headers()

        if self._disabled_reason:
            logger.warning("SystemMetricsRecorder disabled: %s", self._disabled_reason)

    def start(self) -> None:
        """Launch the background thread; safe to call multiple times."""

        if self._disabled_reason:
            logger.warning("Skipping system metrics recorder start: %s", self._disabled_reason)
            return

        with self._start_lock:
            if self._thread and self._thread.is_alive():
                return

            self._thread = threading.Thread(
                target=self._run_loop,
                name="obs360-system-metrics",
                daemon=True,
            )
            self._thread.start()
            logger.info("SystemMetricsRecorder started, posting to: %s", self._metrics_url)

    def stop(self) -> None:
        """Request the background thread to exit and wait for it."""

        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self._interval_seconds + 1)

    def _run_loop(self) -> None:
        """Collect metrics and sleep until the next interval."""

        self._send_metrics()
        while not self._stop_event.wait(self._interval_seconds):
            self._send_metrics()

    def _send_metrics(self) -> None:
        """Build a metrics payload and fire it at the collector."""

        payload = self._build_payload()
        if payload is None:
            return

        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.post(self._metrics_url, json=payload, headers=self._headers)

            if response.status_code >= 300:
                logger.warning(
                    "System metrics rejected (%s): %s",
                    response.status_code,
                    response.text,
                )
        except httpx.RequestError as err:
            logger.warning("Failed to send system metrics to %s: %s", self._metrics_url, err)

    def _build_payload(self) -> Optional[dict]:
        """Convert psutil data into the obs360 metrics schema."""

        if not psutil or self._process is None:
            return None

        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            mem_info = self._process.memory_info()  # type: ignore[attr-defined]
            heap_objects = len(gc.get_objects())
            requests_last_30s = self._count_requests_last_window()
        except Exception as err:
            logger.debug("Unable to collect system metrics: %s", err)
            return None

        # Get database metrics
        db_metrics = db_metrics_collector.get_snapshot_and_reset()

        # Get cache metrics
        cache_stats = get_cache_stats()

        return {
            "serviceName": "badminton_api",
            "serviceEnv": "development" if settings.app_env == "local" else settings.app_env,
            "sdkLanguage": "python",
            "cpuPercent": cpu_percent,
            "memoryAllocBytes": int(mem_info.rss),
            "memorySysBytes": int(mem_info.vms),
            "memoryHeapObjects": heap_objects,
            "goroutinesCount": threading.active_count(),
            "requestsCount": requests_last_30s,
            # Database metrics
            "dbQueryCount": db_metrics.query_count,
            "dbSelectCount": db_metrics.select_count,
            "dbInsertCount": db_metrics.insert_count,
            "dbUpdateCount": db_metrics.update_count,
            "dbDeleteCount": db_metrics.delete_count,
            "dbErrorCount": db_metrics.error_count,
            "dbAvgQueryMs": round(db_metrics.avg_query_ms, 2),
            "dbMaxQueryMs": round(db_metrics.max_query_ms, 2),
            "dbPoolSize": db_metrics.pool_size,
            "dbPoolCheckedOut": db_metrics.pool_checked_out,
            # Cache metrics
            "cacheHits": cache_stats["hits"],
            "cacheMisses": cache_stats["misses"],
            "cacheTotalKeys": cache_stats["total_keys"],
            "cacheHitRate": cache_stats["hit_rate"],
        }

    def record_request(self) -> None:
        """Track a request arrival for rolling window stats."""

        now = time.monotonic()
        with self._request_lock:
            self._request_timestamps.append(now)
            self._prune_requests_locked(now)

    def _count_requests_last_window(self) -> int:
        now = time.monotonic()
        with self._request_lock:
            self._prune_requests_locked(now)
            return len(self._request_timestamps)

    def _prune_requests_locked(self, now: float) -> None:
        cutoff = now - self.REQUEST_WINDOW_SECONDS
        while self._request_timestamps and self._request_timestamps[0] < cutoff:
            self._request_timestamps.popleft()

    def _build_url(self, base_url: str, path: str) -> str:
        """Normalize the URL so we can safely append the path."""

        if not base_url:
            return ""

        base = base_url.rstrip("/")
        suffix = path.lstrip("/")
        return f"{base}/{suffix}"

    def _build_headers(self) -> dict[str, str]:
        """Prepare headers that mirror the existing observability client."""

        headers = {
            "Content-Type": "application/json",
            "X-Obs-Sdk-Language": "python",
        }
        if settings.obs_api_key:
            headers["X-Obs-Api-Key"] = settings.obs_api_key
        return headers


system_metrics_recorder = SystemMetricsRecorder()
system_metrics_recorder.start()
