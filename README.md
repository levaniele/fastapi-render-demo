# Badminton360 API

## Local setup

1) Copy the environment template once:

```powershell
Copy-Item .env.example .env
```

2) Edit `.env` and set `DATABASE_URL` for your local database.

3) Run the server:

```powershell
uvicorn main:app --reload
```

## Production (Render)

Set these environment variables in Render:

- `APP_ENV=production`
- `DATABASE_URL=...`
- `ALLOWED_ORIGINS=https://your-vercel-domain`
- `LOG_LEVEL=INFO`
- `DOCS_ENABLED=false`
