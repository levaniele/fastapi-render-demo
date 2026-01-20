import os
import psycopg2
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Badminton360 API",
    description="API for Badminton360. Health and DB checks + sample endpoints.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

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


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

@app.post("/items", tags=["items"])
def create_item(item: Item):
    """
    Create an item — this is a sample endpoint to show models in Swagger UI.
    """
    return {"ok": True, "item": item.dict()}
