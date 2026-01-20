import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# =============================================================================
# Raw psycopg2 connection (used by existing service functions)
# =============================================================================


def get_db():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        cursor_factory=RealDictCursor,
    )

# =============================================================================
# SQLAlchemy setup (used by new ORM-based services)
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

