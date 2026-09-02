# ============================================================================
# FILE: app/schemas/coach.py
# Coach schemas
# ============================================================================

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CoachBase(BaseModel):
    first_name: str
    last_name: str
    certification_level: Optional[str] = None
    certification_level_id: Optional[int] = None


class CoachCreate(CoachBase):
    club_id: Optional[int] = None
    image_url: Optional[str] = None


class CoachResponse(CoachBase):
    id: int
    slug: str
    club_id: Optional[int] = None
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CoachWithClub(CoachResponse):
    club_name: Optional[str] = None


class CoachList(BaseModel):
    id: int
    first_name: str
    last_name: str
    image_url: Optional[str] = None
    slug: str

    class Config:
        from_attributes = True
