import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.observability_client import setup_db_logging

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =============================================================================
# SQLAlchemy setup with connection pooling
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

# Vercel instances are ephemeral and can scale horizontally. Avoid multiplying a
# process-local connection pool across instances; Neon provides pooling in front
# of Postgres when its pooled connection string is used.
engine_options = {
    "pool_pre_ping": True,
    "echo": False,
}
if os.getenv("VERCEL"):
    engine_options["poolclass"] = NullPool
else:
    engine_options.update(
        pool_size=5,
        max_overflow=5,
        pool_recycle=3600,
    )

engine = create_engine(DATABASE_URL, **engine_options)

# Set up database query logging to observability service
setup_db_logging(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_session():
    """SQLAlchemy session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
