#!/usr/bin/env bash
# Test runner script
# Runs pytest with coverage

set -e

echo "🧪 Running tests..."
pytest --cov=app --cov-report=html --cov-report=term -v

echo ""
echo "✅ Tests complete!"
echo "📊 Coverage report: htmlcov/index.html"
