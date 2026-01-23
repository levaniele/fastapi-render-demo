"""
Services for Authentication operations
All database queries for auth-related endpoints (SQLAlchemy version)
"""

# ============================================================================
# SUMMARY OF SERVICE (AUTH):
# ============================================================================
# get_user_by_email(db, email)         - Fetch user by email
# check_email_exists(db, email)        - Check if email exists
# create_user(db, email, password_hash)- Create new user
# update_user_password(db, email, pw)  - Update user password
# Used by: /auth endpoints (login, register, password reset)

import logging
from sqlalchemy.orm import Session
from app.models import User

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> dict | None:
    """
    Fetch user from database by email.
    Returns: dict with id, email, password_hash, role (or None if not found)
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user.to_dict()
        return None

    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        raise


def check_email_exists(db: Session, email: str) -> bool:
    """
    Check if email already exists in database.
    Returns: True if email exists, False otherwise
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        return user is not None

    except Exception as e:
        logger.error(f"Error checking email existence: {e}")
        raise


def create_user(db: Session, email: str, password_hash: str, role: str = "viewer") -> dict:
    """
    Create new user in database.
    Returns: dict with id, email, role
    """
    try:
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise


def update_user_password(db: Session, email: str, password_hash: str) -> dict | None:
    """
    Update password hash for a user by email.
    Returns: dict with id, email, role (or None if user not found)
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None

        user.password_hash = password_hash
        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user password: {e}")
        raise
