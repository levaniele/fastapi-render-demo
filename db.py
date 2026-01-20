import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Read database URL from env; default to a local sqlite file for dev convenience
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# For SQLite we need connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def test_connection():
    """Attempt a lightweight DB query. Returns (ok: bool, message: str)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "OK"
    except SQLAlchemyError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
