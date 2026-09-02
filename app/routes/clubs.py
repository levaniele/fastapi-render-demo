# ============================================================================
# FILE: app/routes/clubs.py
# REFACTORED VERSION - Service layer integration
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /clubs                     - List all clubs
# GET  /clubs/{slug}              - Get club details by slug
# GET  /clubs/{slug}/players      - List players for a club with rankings

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.schemas import ClubList
from app.services import clubs_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clubs", tags=["Clubs"])


@router.get("", response_model=List[ClubList])
def get_all_clubs(db: Session = Depends(get_db_session)):
    """Fetch all clubs for dashboard and dropdown lists."""
    try:
        clubs = clubs_service.get_all_clubs(db)
        return clubs if clubs else []

    except Exception as e:
        logger.error(f"Error fetching clubs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch clubs",
        )


@router.get("/{slug}")
def get_club_by_slug(slug: str, db: Session = Depends(get_db_session)):
    """Fetch club details with head coach information."""
    try:
        club = clubs_service.get_club_by_slug(db, slug)

        if not club:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Club not found"
            )

        return club

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching club: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch club",
        )


@router.get("/{slug}/players")
def get_club_players(slug: str, db: Session = Depends(get_db_session)):
    """Fetch all players belonging to a club with their rankings."""
    try:
        players = clubs_service.get_club_players(db, slug)
        return players if players else []

    except Exception as e:
        logger.error(f"Error fetching club players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch club players",
        )
