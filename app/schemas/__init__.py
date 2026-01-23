# ============================================================================
# FILE: app/schemas/__init__.py
# Re-exports all schemas for backwards compatibility
# Usage: from app.schemas import LoginRequest, TournamentResponse, etc.
# ============================================================================

# Auth schemas
from app.schemas.auth import (
    LoginRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
)

# Club schemas
from app.schemas.club import (
    ClubBase,
    ClubResponse,
    ClubList,
)

# Player schemas
from app.schemas.player import (
    RankingEntry,
    PlayerBase,
    PlayerResponse,
    PlayerWithClub,
)

# Coach schemas
from app.schemas.coach import (
    CoachBase,
    CoachCreate,
    CoachResponse,
    CoachWithClub,
    CoachList,
)

# Tournament schemas
from app.schemas.tournament import (
    TournamentBase,
    TournamentEventBase,
    TournamentEventResponse,
    TournamentEventCreate,
    TournamentCourtBase,
    TournamentCourtResponse,
    TournamentCourtCreate,
    TournamentTimeBlockBase,
    TournamentTimeBlockResponse,
    TournamentTimeBlockCreate,
    TournamentEntryBase,
    TournamentEntryResponse,
    TournamentEntryCreate,
    TournamentResponse,
    TournamentList,
    TournamentWinnersResponse,
    TournamentWinnersCreate,
    TournamentWinnersUpdate,
    ClubLeaderboardItem,
    PlayerLeaderboardItem,
    OverviewStats,
    TournamentStats,
    StandingsEntry,
    TournamentGroupResponse,
    GroupMemberResponse,
    ALLOWED_TOURNAMENT_STATUSES,
    STATUS_NORMALIZATION_MAP,
    normalize_status,
    TournamentCreate,
    TournamentUpdate,
)

# Match schemas
from app.schemas.match import (
    IndividualMatchBase,
    IndividualMatchResponse,
    DoublesPlayer,
    DoublesMatchResponse,
    MatchTieResponse,
    LineupEntry,
    TeamMember,
    TeamRoster,
)

# Official schemas
from app.schemas.official import (
    OfficialBase,
    UmpireResponse,
    RefereeResponse,
    CertificationLevelResponse,
    CountryResponse,
    UmpireTournamentEntry,
    UmpireProfileWithStats,
)

__all__ = [
    # Auth
    "LoginRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UserResponse",
    # Club
    "ClubBase",
    "ClubResponse",
    "ClubList",
    # Player
    "RankingEntry",
    "PlayerBase",
    "PlayerResponse",
    "PlayerWithClub",
    # Coach
    "CoachBase",
    "CoachCreate",
    "CoachResponse",
    "CoachWithClub",
    "CoachList",
    # Tournament
    "TournamentBase",
    "TournamentEventBase",
    "TournamentEventResponse",
    "TournamentEventCreate",
    "TournamentCourtBase",
    "TournamentCourtResponse",
    "TournamentCourtCreate",
    "TournamentTimeBlockBase",
    "TournamentTimeBlockResponse",
    "TournamentTimeBlockCreate",
    "TournamentEntryBase",
    "TournamentEntryResponse",
    "TournamentEntryCreate",
    "TournamentResponse",
    "TournamentList",
    "TournamentWinnersResponse",
    "TournamentWinnersCreate",
    "TournamentWinnersUpdate",
    "ClubLeaderboardItem",
    "PlayerLeaderboardItem",
    "OverviewStats",
    "TournamentStats",
    "StandingsEntry",
    "TournamentGroupResponse",
    "GroupMemberResponse",
    "ALLOWED_TOURNAMENT_STATUSES",
    "STATUS_NORMALIZATION_MAP",
    "normalize_status",
    "TournamentCreate",
    "TournamentUpdate",
    # Match
    "IndividualMatchBase",
    "IndividualMatchResponse",
    "DoublesPlayer",
    "DoublesMatchResponse",
    "MatchTieResponse",
    "LineupEntry",
    "TeamMember",
    "TeamRoster",
    # Official
    "OfficialBase",
    "UmpireResponse",
    "RefereeResponse",
    "CertificationLevelResponse",
    "CountryResponse",
    "UmpireTournamentEntry",
    "UmpireProfileWithStats",
]
