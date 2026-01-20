"""
Services for Authentication operations
All database queries for auth-related endpoints
"""

import logging
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_user_by_email(db, email: str):
    """
    Fetch user from database by email.
    Returns: dict with id, email, password_hash, role
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            "SELECT id, email, password_hash, role FROM users WHERE email = %s",
            (email,),
        )
        user = cur.fetchone()
        return user

    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        raise
    finally:
        cur.close()


def check_email_exists(db, email: str) -> bool:
    """
    Check if email already exists in database.
    Returns: True if email exists, False otherwise
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        result = cur.fetchone()
        return result is not None

    except Exception as e:
        logger.error(f"Error checking email existence: {e}")
        raise
    finally:
        cur.close()


def create_user(db, email: str, password_hash: str, role: str = "viewer"):
    """
    Create new user in database.
    Returns: dict with id, email, role
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s)
            RETURNING id, email, role
            """,
            (email, password_hash, role),
        )

        user = cur.fetchone()
        db.commit()
        return user

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise
    finally:
        cur.close()


def update_user_password(db, email: str, password_hash: str):
    """
    Update password hash for a user by email.
    Returns: dict with id, email, role
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE email = %s
            RETURNING id, email, role
            """,
            (password_hash, email),
        )
        user = cur.fetchone()
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user password: {e}")
        raise
    finally:
        cur.close()
