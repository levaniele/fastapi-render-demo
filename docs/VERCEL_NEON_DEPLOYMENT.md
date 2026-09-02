# Vercel and Neon deployment

## Required environment variables

Configure these in the Vercel backend project for Preview and Production:

```text
APP_ENV=production
DATABASE_URL=<Neon pooled connection string>
DIRECT_DATABASE_URL=<Neon direct connection string>
SECRET_KEY=<random value of at least 32 characters>
ALLOWED_ORIGINS=https://<frontend-domain>
DOCS_ENABLED=false
OBSERVABILITY_ENABLED=false
```

Use the Neon hostname containing `-pooler` for `DATABASE_URL`. Use the direct
hostname (without `-pooler`) for `DIRECT_DATABASE_URL`, schema migrations, and
database transfer commands.

## Database transfer

Run the transfer from a trusted machine with PostgreSQL client tools installed.
Keep both URLs in local environment variables; never commit them.

```powershell
pg_dump --format=custom --verbose --no-owner --no-acl --file badminton360.dump --dbname $env:SOURCE_DATABASE_URL
pg_restore --verbose --no-owner --no-acl --clean --if-exists --dbname $env:DIRECT_DATABASE_URL badminton360.dump
```

For a new empty Neon database, omit `--clean --if-exists`. For a large or busy
production database, schedule a write freeze or use logical replication instead
of a one-time dump.

## Verify the transfer

```powershell
alembic current
alembic upgrade head
python -c "from app.main import app; print(app.title)"
```

Compare table counts between the source and Neon before switching traffic. Keep
the source database read-only but available until the application has passed its
post-deployment checks.

## Deploy order

1. Create the Neon project and copy both connection strings.
2. Transfer and verify the database using the direct URL.
3. Configure backend environment variables in Vercel and deploy the API.
4. Verify `/`, `/health/simple`, authentication, and one representative read.
5. Set the frontend `BACKEND_URL` to the deployed API origin and deploy the UI.
6. Set `ALLOWED_ORIGINS` to the final frontend domain and redeploy the API.
