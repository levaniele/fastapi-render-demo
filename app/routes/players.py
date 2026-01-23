# ============================================================================
# FILE: app/routes/players.py
# FINAL PRODUCTION VERSION
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /players                              - List all players with club info
# GET  /players/gender/{gender}              - Filter players by gender
# GET  /players/{slug}                       - Get player profile by slug
# GET  /players/{slug}/stats                 - Get player statistics
# GET  /players/{slug}/tournament-history    - Player tournament history
# GET  /players/{slug}/match-history         - Player match history

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.schemas import PlayerWithClub
from app.services import players_service

# Logger for app.routes.players
logger = logging.getLogger(__name__)

# Router setup with prefix /players
router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/", response_model=List[PlayerWithClub])
def get_all_players(db: Session = Depends(get_db_session)):
    """
    Fetches the full player registry.
    Returns players with an array of category rankings (WS, WD, etc.).
    """
    try:
        logger.info("Request received: Fetching all players with aggregated rankings")
        # Ensure players_service.get_all_players_with_clubs(db) is defined in your service layer
        players = players_service.get_all_players_with_clubs(db)

        if players is None:
            return []

        return players
    except Exception as e:
        logger.error(f"Critical Error in GET /players: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@router.get("/gender/{gender}", response_model=List[PlayerWithClub])
def get_by_gender(gender: str, db: Session = Depends(get_db_session)):
    """Filter players by Male or Female."""
    if gender not in ["Male", "Female"]:
        raise HTTPException(
            status_code=400, detail="Invalid gender. Use 'Male' or 'Female'"
        )

    try:
        return players_service.get_players_by_gender(db, gender)
    except Exception as e:
        logger.error(f"Error filtering players by gender ({gender}): {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{slug}", response_model=PlayerWithClub)
def get_player(slug: str, db: Session = Depends(get_db_session)):
    """
    Fetch specific player profile.
    Used for the http://localhost:3000/en/players/[slug] page.
    """
    try:
        logger.info(f"Fetching profile for slug: {slug}")
        player = players_service.get_player_by_slug(db, slug)

        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        return player
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching player ({slug}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{slug}/stats")
def get_stats(slug: str, db: Session = Depends(get_db_session)):
    """Get calculated win/loss record for the profile view."""
    try:
        stats = players_service.get_player_stats(db, slug)
        if not stats:
            raise HTTPException(status_code=404, detail="Stats not found")
        return stats
    except Exception as e:
        logger.error(f"Error calculating stats for {slug}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{slug}/tournament-history")
def get_tournaments(slug: str, db: Session = Depends(get_db_session)):
    """Get history of tournament placements for the profile view."""
    try:
        return players_service.get_tournament_history(db, slug)
    except Exception as e:
        logger.error(f"Error fetching tournament history for {slug}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{slug}/match-history")
def get_matches(slug: str, db: Session = Depends(get_db_session)):
    """Get the last 10 individual matches for the profile view."""
    try:
        return players_service.get_player_match_history(db, slug)
    except Exception as e:
        logger.error(f"Error fetching match history for {slug}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
