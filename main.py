import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2 import pool

from settings import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("app")

docs_enabled = settings.docs_enabled and not settings.is_production

app = FastAPI(
    title="Badminton360 API",
    description="API for Badminton360. Health and DB checks + sample endpoints.",
    version="1.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

allowed_origins = settings.parsed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db_pool: Optional[pool.SimpleConnectionPool] = None


def _ensure_ssl(db_url: str) -> str:
    if "sslmode=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{sep}sslmode=require"
    return db_url


def _create_pool() -> pool.SimpleConnectionPool:
    db_url = settings.database_url.strip()
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    db_url = _ensure_ssl(db_url)
    return pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        dsn=db_url,
        connect_timeout=5,
    )


def _reset_pool() -> None:
    global _db_pool
    if _db_pool is not None:
        _db_pool.closeall()
    _db_pool = _create_pool()


def _connect():
    global _db_pool
    if _db_pool is None:
        _db_pool = _create_pool()
    try:
        conn = _db_pool.getconn()
        if conn.closed != 0:
            _db_pool.putconn(conn, close=True)
            conn = _db_pool.getconn()
        return conn
    except Exception:
        _reset_pool()
        return _db_pool.getconn()


def _release_conn(conn) -> None:
    if _db_pool is not None:
        _db_pool.putconn(conn)


@app.on_event("startup")
def _startup() -> None:
    global _db_pool
    if _db_pool is None:
        _db_pool = _create_pool()


@app.on_event("shutdown")
def _shutdown() -> None:
    global _db_pool
    if _db_pool is not None:
        _db_pool.closeall()
        _db_pool = None


@app.get("/health")
def health():
    return {"ok": True, "service": "badminton360", "db": "not_checked"}


@app.get("/db/health")
def db_health():
    for attempt in range(2):
        try:
            conn = _connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    val = cur.fetchone()[0]
                return {"ok": True, "db": "connected", "select_1": val}
            finally:
                _release_conn(conn)
        except psycopg2.OperationalError:
            logger.warning("DB health check failed, resetting pool", exc_info=True)
            _reset_pool()
        except Exception as e:
            logger.exception("DB health check failed")
            if settings.is_production:
                return {"ok": False, "db": "error"}
            return {"ok": False, "db": "error", "error": str(e)}

    if settings.is_production:
        return {"ok": False, "db": "error"}
    return {"ok": False, "db": "error", "error": "DB connection failed after retry"}


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


@app.post("/items", tags=["items"])
def create_item(item: Item):
    """
    Create an item; this is a sample endpoint to show models in Swagger UI.
    """
    return {"ok": True, "item": item.dict()}
