"""
Trace context management for distributed tracing.
Uses context variables to propagate trace IDs across async boundaries.
"""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TraceContext:
    """Immutable trace context containing trace and span identifiers."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None


_ctx: ContextVar[Optional[TraceContext]] = ContextVar("trace_context", default=None)


def set_trace_context(
    trace_id: str, 
    span_id: str, 
    parent_span_id: Optional[str] = None
):
    """
    Set the trace context for the current async context.
    
    Args:
        trace_id: Unique identifier for the entire trace (32-char hex)
        span_id: Unique identifier for this span (16-char hex)
        parent_span_id: Optional parent span identifier
        
    Returns:
        Token that can be used to reset the context
    """
    return _ctx.set(
        TraceContext(
            trace_id=trace_id, 
            span_id=span_id, 
            parent_span_id=parent_span_id
        )
    )


def reset_trace_context(token) -> None:
    """
    Reset the trace context to its previous value.
    
    Args:
        token: Token returned from set_trace_context()
    """
    _ctx.reset(token)


def get_trace_context() -> Optional[TraceContext]:
    """
    Get the current trace context.
    
    Returns:
        Current TraceContext or None if not set
    """
    return _ctx.get()
