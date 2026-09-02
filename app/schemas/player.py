# ============================================================================
# FILE: app/schemas/player.py
# Player schemas
# ============================================================================

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


class RankingEntry(BaseModel):
    category: str
    rank: int


class PlayerBase(BaseModel):
    first_name: str
    last_name: str
    gender: str
    birth_date: Optional[date] = None
    nationality_code: Optional[str] = None


class PlayerResponse(PlayerBase):
    id: int
    slug: str
    club_id: Optional[int] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    rankings: List[RankingEntry] = []

    class Config:
        from_attributes = True


class PlayerWithClub(PlayerResponse):
    club_name: Optional[str] = None
    club_logo: Optional[str] = None
    metric_speed: int = 85
    metric_stamina: int = 78
    metric_agility: int = 92
    metric_power: int = 74

    class Config:
        from_attributes = True
