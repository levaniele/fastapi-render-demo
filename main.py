import os
import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Badminton360 API")

# --- CORS (keep your Vercel domain here) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://verceldev-seven.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_db_url() -> str:
    db_url = os.getenv("DATABASE_URL", "").strip()
    return db_url

def _connect():
    db_url = _get_db_url()
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    # Neon typically needs SSL. If your URL already has sslmode=require, this is fine.
    # If it doesn't, we enforce it.
    if "sslmode=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{sep}sslmode=require"

    return psycopg2.connect(db_url)

@app.get("/health")
def health():
    return {"ok": True, "service": "badminton360", "db": "not_checked"}

@app.get("/db/health")
def db_health():
    try:
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                val = cur.fetchone()[0]
            return {"ok": True, "db": "connected", "select_1": val}
        finally:
            conn.close()
    except Exception as e:
        return {"ok": False, "db": "error", "error": str(e)}