"""Compatibility ASGI entry point for hosts that run ``uvicorn main:app``."""

from app.main import app

__all__ = ["app"]
