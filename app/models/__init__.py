# ============================================================================
# FILE: app/models/__init__.py
# Exports all ORM models for convenient imports
# Usage: from app.models import Tournament, User, Player
# ============================================================================

from app.models.tournament import (
    Tournament, 
    TournamentVenue, 
    TournamentEvent, 
    TournamentCourt, 
    TournamentTimeBlock, 
    TournamentEntry, 
    TournamentWinner,
    TournamentGroup,
    TournamentGroupMember,
    TournamentLineup,
    TournamentCoach,
    TournamentUmpire
)
from app.models.user import User
from app.models.player import Player
from app.models.club import Club
from app.models.coach import Coach
from app.models.certification_level import CertificationLevel
from app.models.match import MatchTie, IndividualMatch, MatchRally
from app.models.organization import Organization
from app.models.official import Umpire, Referee

__all__ = [
    "Tournament", 
    "TournamentVenue", 
    "TournamentEvent", 
    "TournamentCourt", 
    "TournamentTimeBlock", 
    "TournamentEntry", 
    "TournamentWinner",
    "TournamentGroup",
    "TournamentGroupMember",
    "TournamentLineup",
    "TournamentCoach",
    "TournamentUmpire",
    "User", 
    "Player",
    "Club",
    "Coach",
    "CertificationLevel",
    "MatchTie",
    "IndividualMatch",
    "MatchRally",
    "Organization",
    "Umpire",
    "Referee"
]
