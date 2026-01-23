import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =============================================================================
# Compatibility helper: return raw DB-API connection from SQLAlchemy engine
# Prefer using `get_db_session()` (SQLAlchemy Session) in new code.
# =============================================================================

def get_db():
    """Return a raw DB-API connection (compatibility).
    
    DEPRECATED: This function is deprecated and will be removed.
    Use SQLAlchemy Session via `get_db_session()` instead.
    """
    import warnings
    warnings.warn("get_db() is deprecated. Use get_db_session() instead.", DeprecationWarning, stacklevel=2)
    return engine.raw_connection()

# =============================================================================
# SQLAlchemy setup (used by ORM-based services)
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    port_segment = f":{db_port}" if db_port else ""
    DATABASE_URL = (
        f"postgresql://{db_user}:{db_password}@{db_host}{port_segment}/{db_name}"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_session():
    """SQLAlchemy session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

