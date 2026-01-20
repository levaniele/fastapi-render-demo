from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time

# ============================================================================
# FILE: app/schemas.py
# FINAL VERSION - Includes Auth, Players, Clubs, Tournaments, and Rosters
# ============================================================================


# ============================================================================
# 1. AUTH SCHEMAS
# ============================================================================


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# 2. CLUB SCHEMAS
# ============================================================================


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


# ============================================================================
# 3. PLAYER SCHEMAS
# ============================================================================


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

    # 🔴 CHANGE THIS LINE
    # FROM: created_at: datetime
    # TO:
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


# ============================================================================
# 4. COACH SCHEMAS
# ============================================================================


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


# ============================================================================
# 5. TOURNAMENT SCHEMAS
# ============================================================================


class TournamentBase(BaseModel):
    name: str
    slug: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "DRAFT"
    logo_url: Optional[str] = None


class TournamentEventBase(BaseModel):
    event_name: str
    discipline: str
    category: str
    level: str
    scoring_format: str
    max_entries: int
    entry_fee: Optional[float] = None
    currency: Optional[str] = None
    member_perks: Optional[str] = None
    draw_type: Optional[str] = None
    draw_setup: Optional[Dict[str, Any]] = None
    generation_rules: Optional[Dict[str, Any]] = None
    seeding_mode: Optional[str] = None
    lock_entries: Optional[bool] = False
    publish_bracket_preview: Optional[bool] = False
    bracket_visibility: Optional[str] = None


class TournamentEventResponse(TournamentEventBase):
    id: int

    class Config:
        from_attributes = True


class TournamentEventCreate(TournamentEventBase):
    pass


class TournamentCourtBase(BaseModel):
    court_name: str
    court_number: int
    venue_label: Optional[str] = None


class TournamentCourtResponse(TournamentCourtBase):
    id: int

    class Config:
        from_attributes = True


class TournamentCourtCreate(TournamentCourtBase):
    pass


class TournamentTimeBlockBase(BaseModel):
    block_type: str
    block_label: Optional[str] = None
    block_date: date
    start_time: time
    end_time: time
    lunch_break_enabled: bool = False
    break_start_time: Optional[time] = None
    break_end_time: Optional[time] = None


class TournamentTimeBlockResponse(TournamentTimeBlockBase):
    id: int

    class Config:
        from_attributes = True


class TournamentTimeBlockCreate(TournamentTimeBlockBase):
    pass


class TournamentEntryBase(BaseModel):
    entry_name: str
    entry_type: str
    entry_category: Optional[str] = None
    entry_discipline: Optional[str] = None
    approval_status: Optional[str] = None
    event_id: Optional[int] = None


class TournamentEntryResponse(TournamentEntryBase):
    id: int

    class Config:
        from_attributes = True


class TournamentEntryCreate(TournamentEntryBase):
    pass


class TournamentResponse(TournamentBase):
    id: int
    created_at: datetime

    # Phase 1 columns
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timezone: Optional[str] = None
    organizer_organization_id: Optional[int] = None

    # Optional registration
    registration_deadline_at: Optional[datetime] = None

    # Optional branding
    banner_url: Optional[str] = None

    # Optional invitations
    invites_enabled: Optional[bool] = None
    invites_open_at: Optional[datetime] = None
    invites_close_at: Optional[datetime] = None

    # Registration settings
    public_registration: Optional[bool] = None
    allow_waitlist: Optional[bool] = None
    show_bracket_publicly: Optional[bool] = None
    auto_approve_entries: Optional[bool] = None
    allow_entry_editing: Optional[bool] = None

    # Venue/scheduling settings
    venue_mode: Optional[str] = None
    avg_match_duration_min: Optional[int] = None
    match_buffer_min: Optional[int] = None
    enforce_quiet_hours: Optional[bool] = None

    # Phase tracking columns
    current_phase: int = 1  # Where user should continue (1..7)
    last_completed_phase: int = 0  # Last fully completed phase (0..7)
    readiness_percent: int = 0  # Readiness percent (0..100)
    tournament_venue: Optional[Dict[str, Any]] = None
    events: List[TournamentEventResponse] = []
    courts: List[TournamentCourtResponse] = []
    time_blocks: List[TournamentTimeBlockResponse] = []
    entries: List[TournamentEntryResponse] = []

    class Config:
        from_attributes = True


class TournamentList(BaseModel):
    id: int
    name: str
    slug: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    logo_url: Optional[str] = None

    # Phase tracking columns
    current_phase: int = 1  # Where user should continue (1..7)
    last_completed_phase: int = 0  # Last fully completed phase (0..7)
    readiness_percent: int = 0  # Readiness percent (0..100)
    tournament_venue: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TournamentWinnersResponse(BaseModel):
    tournament_id: int
    tournament_name: str
    tournament_slug: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    first_place_club_id: Optional[int] = None
    first_place_club_name: Optional[str] = None
    second_place_club_id: Optional[int] = None
    second_place_club_name: Optional[str] = None
    third_place_club_id: Optional[int] = None
    third_place_club_name: Optional[str] = None

    first_place_player_id: Optional[int] = None
    first_place_player_name: Optional[str] = None
    second_place_player_id: Optional[int] = None
    second_place_player_name: Optional[str] = None
    third_place_player_id: Optional[int] = None
    third_place_player_name: Optional[str] = None

    class Config:
        from_attributes = True


class TournamentWinnersCreate(BaseModel):
    tournament_id: int
    first_place_club_id: Optional[int] = None
    second_place_club_id: Optional[int] = None
    third_place_club_id: Optional[int] = None
    first_place_player_id: Optional[int] = None
    second_place_player_id: Optional[int] = None
    third_place_player_id: Optional[int] = None


class TournamentWinnersUpdate(BaseModel):
    first_place_club_id: Optional[int] = None
    second_place_club_id: Optional[int] = None
    third_place_club_id: Optional[int] = None
    first_place_player_id: Optional[int] = None
    second_place_player_id: Optional[int] = None
    third_place_player_id: Optional[int] = None



# --- NEW STATS MODELS (Added to support the Dashboard) ---


class ClubLeaderboardItem(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    matches_won: int


class PlayerLeaderboardItem(BaseModel):
    id: int
    first_name: str
    last_name: str
    slug: str
    image_url: Optional[str] = None
    club_name: Optional[str] = None
    club_logo: Optional[str] = None
    matches_won: int


class OverviewStats(BaseModel):
    total_rallies: int
    team1_serve_efficiency: int
    team2_serve_efficiency: int
    rallies_per_set: Dict[str, int]
    club_leaderboard: List[ClubLeaderboardItem]


# ✅ UPDATED: Matches the new nested JSON structure
class TournamentStats(BaseModel):
    # Top-level fields expected by the test and service
    total_matches: int
    total_duration: int = 0
    total_points: int = 0
    mvp: Optional[str] = None
    total_players: int
    total_clubs: int
    overview_statistics: OverviewStats
    player_leaderboard: List[PlayerLeaderboardItem]

    class Config:
        from_attributes = True


# --- END NEW STATS MODELS ---


class StandingsEntry(BaseModel):
    club_id: int
    club_name: str
    club_logo: Optional[str] = None
    matches_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    points: int = 0
    head_to_head: Dict = {}


class TournamentGroupResponse(BaseModel):
    id: int
    tournament_id: int
    group_name: str

    class Config:
        from_attributes = True


class GroupMemberResponse(BaseModel):
    id: int
    group_id: int
    club_id: int
    club_name: str
    club_logo: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# 6. MATCH & LINEUP SCHEMAS
# ============================================================================


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
# 7. TEAM ROSTER SCHEMAS (Fixes ImportError: TeamRoster)
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


# ============================================================================
# 8. MISC SCHEMAS
# ============================================================================


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


# ============================================================================
# ADD TO: app/schemas.py (Place this near Official/Umpire schemas)
# ============================================================================


# 1. Schema for the list of tournaments in the umpire profile
class UmpireTournamentEntry(BaseModel):
    id: int
    name: str
    slug: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    logo_url: Optional[str] = None


# 2. The main response schema that caused your error
class UmpireProfileWithStats(UmpireResponse):
    total_matches: int = 0
    total_tournaments: int = 0
    matches: List[IndividualMatchResponse] = []
    tournaments: List[UmpireTournamentEntry] = []

    class Config:
        from_attributes = True


ALLOWED_TOURNAMENT_STATUSES = {
    "DRAFT",
    "Upcoming",
    "In Progress",
    "Finished",
    "Cancelled",
}

# Mapping from frontend-provided values (with typos/casing) to canonical DB values
STATUS_NORMALIZATION_MAP = {
    "draft": "DRAFT",
    "draf": "DRAFT",
    "in progres": "In Progress",
    "in progress": "In Progress",
    "inprogress": "In Progress",
    "finished": "Finished",
    "upcoming": "Upcoming",
    "publish": "Upcoming",
    "published": "Upcoming",
    "publishd": "Upcoming",
    "canceled": "Cancelled",
    "cancelled": "Cancelled",
    "canceled abandones": "Cancelled",
    "cancelled abandones": "Cancelled",
}


def normalize_status(value: str) -> str:
    if value is None:
        return value
    key = value.strip().lower()
    # Direct mapping
    if key in STATUS_NORMALIZATION_MAP:
        return STATUS_NORMALIZATION_MAP[key]
    # Accept exact DB canonical values (case-insensitive)
    for canonical in ALLOWED_TOURNAMENT_STATUSES:
        if key == canonical.lower():
            return canonical
    # Fallback: title case the value and hope it matches DB allowed set
    title_cased = value.strip().title()
    if title_cased in ALLOWED_TOURNAMENT_STATUSES:
        return title_cased
    return value


class TournamentCreate(BaseModel):
    """Schema for creating a tournament - matches actual DB schema."""

    # Required
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    start_date: date
    end_date: date
    timezone: str = Field(..., max_length=64)
    organizer_organization_id: int

    # Optional registration
    status: str = Field(default="DRAFT", max_length=50)

    @field_validator("status")
    def validate_status(cls, v):
        normalized = normalize_status(v)
        if normalized not in ALLOWED_TOURNAMENT_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed (after normalization): {sorted(ALLOWED_TOURNAMENT_STATUSES)}"
            )
        return normalized

    # Optional registration
    registration_deadline_at: Optional[datetime] = None

    # Optional branding
    logo_url: Optional[str] = Field(default=None, max_length=255)
    banner_url: Optional[str] = Field(default=None, max_length=255)

    # Optional invitations
    invites_enabled: bool = False
    invites_open_at: Optional[datetime] = None
    invites_close_at: Optional[datetime] = None

    # Registration settings
    public_registration: bool = True
    allow_waitlist: bool = False
    show_bracket_publicly: bool = False
    auto_approve_entries: bool = False
    allow_entry_editing: bool = True

    # Venue/scheduling settings
    venue_mode: str = Field(default="single", max_length=10)
    avg_match_duration_min: Optional[int] = None
    match_buffer_min: Optional[int] = None
    enforce_quiet_hours: bool = False

    # Optional venue info (tournament_venues table)
    venue_name: Optional[str] = Field(default=None, max_length=255)
    venue_city: Optional[str] = Field(default=None, max_length=255)
    venue_country_code: Optional[str] = Field(default=None, max_length=10)

    # Nested tournament data
    events: Optional[List[TournamentEventCreate]] = None
    courts: Optional[List[TournamentCourtCreate]] = None
    time_blocks: Optional[List[TournamentTimeBlockCreate]] = None
    entries: Optional[List[TournamentEntryCreate]] = None

    # Phase tracking columns (optional with defaults)
    current_phase: int = Field(
        default=1, ge=1, le=7
    )  # Where user should continue (1..7)
    last_completed_phase: int = Field(
        default=0, ge=0, le=7
    )  # Last fully completed phase (0..7)
    readiness_percent: int = Field(
        default=0, ge=0, le=100
    )  # Readiness percent (0..100)

    class Config:
        from_attributes = True


class TournamentUpdate(BaseModel):
    """Schema for updating a tournament - all fields optional."""

    name: Optional[str] = Field(default=None, max_length=100)
    slug: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timezone: Optional[str] = Field(default=None, max_length=64)
    organizer_organization_id: Optional[int] = None

    status: Optional[str] = Field(default=None, max_length=50)

    @field_validator("status")
    def validate_status_optional(cls, v):
        if v is None:
            return v
        normalized = normalize_status(v)
        if normalized not in ALLOWED_TOURNAMENT_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Allowed (after normalization): {sorted(ALLOWED_TOURNAMENT_STATUSES)}"
            )
        return normalized

    # Optional registration
    registration_deadline_at: Optional[datetime] = None

    # Optional branding
    logo_url: Optional[str] = Field(default=None, max_length=255)
    banner_url: Optional[str] = Field(default=None, max_length=255)

    # Optional invitations
    invites_enabled: Optional[bool] = None
    invites_open_at: Optional[datetime] = None
    invites_close_at: Optional[datetime] = None

    # Registration settings
    public_registration: Optional[bool] = None
    allow_waitlist: Optional[bool] = None
    show_bracket_publicly: Optional[bool] = None
    auto_approve_entries: Optional[bool] = None
    allow_entry_editing: Optional[bool] = None

    # Venue/scheduling settings
    venue_mode: Optional[str] = Field(default=None, max_length=10)
    avg_match_duration_min: Optional[int] = None
    match_buffer_min: Optional[int] = None
    enforce_quiet_hours: Optional[bool] = None

    # Optional venue info (tournament_venues table)
    venue_name: Optional[str] = Field(default=None, max_length=255)
    venue_city: Optional[str] = Field(default=None, max_length=255)
    venue_country_code: Optional[str] = Field(default=None, max_length=10)

    # Nested tournament data
    events: Optional[List[TournamentEventCreate]] = None
    courts: Optional[List[TournamentCourtCreate]] = None
    time_blocks: Optional[List[TournamentTimeBlockCreate]] = None
    entries: Optional[List[TournamentEntryCreate]] = None

    # Phase tracking columns (optional for update)
    current_phase: Optional[int] = Field(
        default=None, ge=1, le=7
    )  # Where user should continue (1..7)
    last_completed_phase: Optional[int] = Field(
        default=None, ge=0, le=7
    )  # Last fully completed phase (0..7)
    readiness_percent: Optional[int] = Field(
        default=None, ge=0, le=100
    )  # Readiness percent (0..100)

    class Config:
        from_attributes = True
