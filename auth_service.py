import logging

from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_user_by_email(db, email: str):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id, email, password_hash, role FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()
    except Exception as exc:
        logger.error("Error fetching user by email: %s", exc)
        raise
    finally:
        cur.close()


def check_email_exists(db, email: str) -> bool:
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        return cur.fetchone() is not None
    except Exception as exc:
        logger.error("Error checking email existence: %s", exc)
        raise
    finally:
        cur.close()


def create_user(db, email: str, password_hash: str, role: str = "viewer"):
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
    except Exception as exc:
        db.rollback()
        logger.error("Error creating user: %s", exc)
        raise
    finally:
        cur.close()


def get_user_by_id(db, user_id: int):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id, email, password_hash, role FROM users WHERE id = %s",
            (user_id,),
        )
        return cur.fetchone()
    except Exception as exc:
        logger.error("Error fetching user by id: %s", exc)
        raise
    finally:
        cur.close()


def update_password(db, user_id: int, password_hash: str):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s RETURNING id, email, role",
            (password_hash, user_id),
        )
        user = cur.fetchone()
        db.commit()
        return user
    except Exception as exc:
        db.rollback()
        logger.error("Error updating password: %s", exc)
        raise
    finally:
        cur.close()

