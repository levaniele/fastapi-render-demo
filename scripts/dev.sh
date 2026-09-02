#!/usr/bin/env bash
# Development server startup script
# Runs FastAPI with hot reload for local development

set -e

echo "🚀 Starting development server..."
echo "📍 URL: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
