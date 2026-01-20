import psycopg2
from psycopg2.extras import RealDictCursor

from settings import get_settings


def get_db():
    settings = get_settings()
    conn = psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()
