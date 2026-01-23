# ============================================================================
# FILE: app/models/user.py
# ORM Model for the 'users' table
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")

    # Timestamps (if they exist in your table - safe to include)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def to_dict(self):
        """Convert to dictionary for backwards compatibility with existing code."""
        return {
            "id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
        }
