# ============================================================================
# FILE: app/models/club.py
# ORM Model for the 'clubs' table
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    location = Column(String(255), nullable=True)
    logo_url = Column(String(255), nullable=True)
    head_coach_id = Column(Integer, nullable=True) # Assuming simple integer for now, add ForeignKey if Coach model exists

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships can be added here as needed
    # players = relationship("Player", back_populates="club")
