import secrets
import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.trace_context import set_trace_context, reset_trace_context
from app.core.observability_client import log_event
from app.core.system_metrics import system_metrics_recorder


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Extract or Generate Trace ID
        trace_id = request.headers.get("X-Trace-Id")
        if not trace_id:
            trace_id = secrets.token_hex(16)  # 32 hex chars

        # 2. Extract or Generate Span ID
        span_id = request.headers.get("X-Span-Id")
        if not span_id:
            span_id = secrets.token_hex(8)  # 16 hex chars

        # 3. Extract Parent Span ID (optional)
        parent_span_id = request.headers.get("X-Parent-Span-Id")

        # 4. Attach to Request State
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        request.state.parent_span_id = parent_span_id

        # 5. Set trace context for async propagation
        token = set_trace_context(trace_id, span_id, parent_span_id)
        start = time.perf_counter()
        response: Response | None = None

        try:
            # 6. Process Request
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id
            return response
        finally:
            system_metrics_recorder.record_request()
            duration_ms = (time.perf_counter() - start) * 1000.0
            status = int(getattr(response, "status_code", 500) or 500)

            # 7. Log HTTP request asynchronously to avoid adding network latency to responses.
            asyncio.create_task(
                log_event(
                    level="info" if status < 400 else "warn" if status < 500 else "error",
                    type="http",
                    name="http.request",
                    attributes={
                        "method": request.method,
                        "path": request.url.path,
                    },
                    status_code=status,
                    duration_ms=duration_ms,
                )
            )

            # 8. Reset trace context
            reset_trace_context(token)
