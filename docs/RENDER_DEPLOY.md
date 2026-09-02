# Render Deployment Guide

## Quick Setup

### 1. **Render Dashboard**
- Go to [render.com](https://render.com)
- Click "New +" → "Web Service"
- Connect your GitHub repo

### 2. **Configuration**

**Build Command:**
```bash
./build.sh
```

**Start Command:**
```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

### 3. **Environment Variables**

Add these in Render dashboard:

```bash
# Required
APP_ENV=production
DATABASE_URL=<your-postgres-url>  # Render provides this
SECRET_KEY=<generate-strong-key>  # Use: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Optional
ALLOWED_ORIGINS=https://yourdomain.com
DOCS_ENABLED=false
DOCS_IN_PRODUCTION=false
OBSERVABILITY_ENABLED=false
OBSERVABILITY_URL=<your-go-service-url>
```

### 4. **Database**
- Create PostgreSQL database in Render
- Copy the "Internal Database URL"
- Paste as `DATABASE_URL` environment variable

---

## What `pip freeze` Does

**`pip freeze`** outputs all installed packages with exact versions:

```bash
# Run this to see current versions:
pip freeze

# Output example:
fastapi==0.109.2
uvicorn==0.27.1
psycopg2-binary==2.9.9
```

**Why pin versions?**
- ✅ Reproducible builds (same versions every time)
- ✅ Prevents breaking changes from new releases
- ✅ Easier debugging (know exact versions)

**Your `requirements.txt` is now pinned!** ✅

---

## Deployment Checklist

- [x] Pin dependency versions
- [x] Add gunicorn for production
- [x] Create build.sh script
- [ ] Set environment variables in Render
- [ ] Connect GitHub repo
- [ ] Deploy!

---

## Testing Locally

Test the production setup locally:

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with gunicorn (like production)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Visit: http://localhost:8000

---

## Troubleshooting

**Build fails?**
- Check `build.sh` has execute permissions
- Verify all environment variables are set
- Check Render build logs

**App crashes?**
- Check `SECRET_KEY` is set and strong (32+ chars)
- Verify `DATABASE_URL` is correct
- Check Render runtime logs

**Database errors?**
- Ensure migrations ran: `alembic upgrade head`
- Check DATABASE_URL format
- Verify database is accessible

---

## Production Checklist

✅ **Security**
- Strong SECRET_KEY (32+ characters)
- DOCS_ENABLED=false
- HTTPS only (Render provides this)

✅ **Performance**
- Gunicorn with 4 workers
- Database connection pooling configured
- Uvicorn worker class for async

✅ **Monitoring**
- Observability service connected
- Health check endpoint: `/health`
- Error tracking (optional: add Sentry)
