# ============================================================================
# FILE: app/schemas/official.py
# Official (Umpire, Referee) schemas
# ============================================================================

from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from app.schemas.match import IndividualMatchResponse


class OfficialBase(BaseModel):
    first_name: str
    last_name: str
    slug: str
    image_url: Optional[str] = None
    certification_level: Optional[str] = None
    nationality_code: Optional[str] = None


class UmpireResponse(OfficialBase):
    id: int

    class Config:
        from_attributes = True


class RefereeResponse(OfficialBase):
    id: int

    class Config:
        from_attributes = True


class CertificationLevelResponse(BaseModel):
    id: int
    level_code: str
    level_name: str
    level_type: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CountryResponse(BaseModel):
    code: str
    name: str
    flag_url: Optional[str] = None

    class Config:
        from_attributes = True


class UmpireTournamentEntry(BaseModel):
    id: int
    name: str
    slug: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    logo_url: Optional[str] = None


class UmpireProfileWithStats(UmpireResponse):
    total_matches: int = 0
    total_tournaments: int = 0
    matches: List[IndividualMatchResponse] = []
    tournaments: List[UmpireTournamentEntry] = []

    class Config:
        from_attributes = True
