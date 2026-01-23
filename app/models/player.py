# ============================================================================
# FILE: app/models/player.py
# ORM Model for the 'players' table
# ============================================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    first_name_geo = Column(String(100), nullable=True)
    last_name_geo = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=False)
    birth_date = Column(Date, nullable=True)
    nationality_code = Column(String(10), nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    image_url = Column(String(255), nullable=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True, index=True)

    # Performance metrics
    metric_speed = Column(Integer, nullable=True, default=85)
    metric_stamina = Column(Integer, nullable=True, default=78)
    metric_agility = Column(Integer, nullable=True, default=92)
    metric_power = Column(Integer, nullable=True, default=74)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "nationality_code": self.nationality_code,
            "slug": self.slug,
            "image_url": self.image_url,
            "club_id": self.club_id,
            "metric_speed": self.metric_speed or 85,
            "metric_stamina": self.metric_stamina or 78,
            "metric_agility": self.metric_agility or 92,
            "metric_power": self.metric_power or 74,
            "created_at": self.created_at,
        }
