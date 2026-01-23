# ============================================================================
# FILE: app/schemas/match.py
# Match & Lineup schemas
# ============================================================================

from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time


class IndividualMatchBase(BaseModel):
    id: int
    tie_id: int
    match_type: str
    category: str
    set_1_score: Optional[str] = "[default]"
    set_2_score: Optional[str] = "[default]"
    set_3_score: Optional[str] = None
    duration_minutes: Optional[int] = None


class IndividualMatchResponse(IndividualMatchBase):
    player_1_name: Optional[str] = None
    player_2_name: Optional[str] = None
    winner_name: Optional[str] = None
    umpire_name: Optional[str] = "TBD"

    class Config:
        from_attributes = True


class DoublesPlayer(BaseModel):
    player_id: int
    player_name: str
    team_side: int  # 1 or 2


class DoublesMatchResponse(IndividualMatchResponse):
    team_1_players: List[DoublesPlayer] = []
    team_2_players: List[DoublesPlayer] = []


class MatchTieResponse(BaseModel):
    id: int
    group_id: int
    club_1_id: int
    club_2_id: int
    club_1_name: str
    club_1_logo: Optional[str] = None
    club_2_name: str
    club_2_logo: Optional[str] = None
    overall_score: str
    tie_date: Optional[date] = None
    tie_time: Optional[time] = None
    stage_label: str
    individual_matches: List[IndividualMatchResponse]


class LineupEntry(BaseModel):
    id: int
    tournament_id: int
    category: str
    player_id: Optional[int] = None
    player_2_id: Optional[int] = None
    player_name: Optional[str] = None
    player_2_name: Optional[str] = None
    club_id: Optional[int] = None
    club_name: Optional[str] = None
    finishing_place: Optional[int] = None


# ============================================================================
# Team Roster Schemas
# ============================================================================


class TeamMember(BaseModel):
    category: str
    player1_name: str
    player2_name: Optional[str] = None


class TeamRoster(BaseModel):
    club_id: int
    club_name: str
    club_logo: Optional[str] = None
    coach_name: Optional[str] = None
    roster: List[TeamMember]
