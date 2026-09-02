#!/usr/bin/env bash
# Database migration script
# Runs Alembic migrations

set -e

echo "🗄️  Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete!"
