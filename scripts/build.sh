#!/usr/bin/env bash
# Render build script
# This script runs during deployment on Render

set -o errexit  # Exit on error

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
alembic upgrade head

echo "✅ Build complete!"
