# ============================================================================
# FILE: app/schemas/club.py
# Club schemas
# ============================================================================

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClubBase(BaseModel):
    name: str
    slug: str
    location: Optional[str] = None
    logo_url: Optional[str] = None


class ClubResponse(ClubBase):
    id: int
    head_coach_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClubList(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True
