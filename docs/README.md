# Documentation

This directory contains all project documentation.

## Contents

### Deployment
- [`RENDER_DEPLOY.md`](RENDER_DEPLOY.md) - Complete guide for deploying to Render
- [`VERSIONING.md`](VERSIONING.md) - Git-based automatic versioning guide

### Database
- [`schema.sql`](schema.sql) - Complete database schema
- [`badminton360_erd.svg`](badminton360_erd.svg) - Entity Relationship Diagram

## Quick Links

**Getting Started:**
1. Read the main [README.md](../README.md)
2. Set up environment variables from [.env.example](../.env.example)
3. Run database migrations: `alembic upgrade head`
4. Start development server: `uvicorn app.main:app --reload`

**Deploying to Production:**
1. Follow [RENDER_DEPLOY.md](RENDER_DEPLOY.md)
2. Set up environment variables
3. Push to GitHub
4. Deploy on Render

**Testing:**
See [tests/README.md](../tests/README.md) for testing guide.

**Versioning:**
See [VERSIONING.md](VERSIONING.md) for automatic version management.
