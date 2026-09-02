# ============================================================================
# FILE: app/routes/matches.py
# REFACTORED VERSION - Service layer integration
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /matches/ties/{tie_id}                 - Get match tie with individual matches
# GET  /matches/individual/{match_id}         - Get individual match details
# GET  /matches/category/{category}           - List matches by category
# GET  /matches/recent                        - Get recent matches
# GET  /matches/stats/player/{player_id}      - Player match stats
# GET  /matches/stats/head-to-head            - Head-to-head statistics

from fastapi import APIRouter, HTTPException, status, Depends
import logging
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.services import matches_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matches", tags=["Matches"])


# ============================================================================
# MATCH TIE ENDPOINTS
# ============================================================================


@router.get("/ties/{tie_id}")
def get_match_tie_by_id(tie_id: int, db: Session = Depends(get_db_session)):
    """
    Fetch complete match tie details including all individual matches.
    """
    try:
        tie = matches_service.get_match_tie_by_id(db, tie_id)

        if not tie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match tie with ID {tie_id} not found",
            )

        return tie

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching match tie: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch match tie",
        )


# ============================================================================
# INDIVIDUAL MATCH ENDPOINTS
# ============================================================================


@router.get("/individual/{match_id}")
def get_individual_match(match_id: int, db: Session = Depends(get_db_session)):
    """
    Fetch detailed information for a single individual match.
    Handles both singles and doubles matches.
    """
    try:
        match = matches_service.get_individual_match(db, match_id)

        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Match with ID {match_id} not found",
            )

        return match

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching individual match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch match",
        )


@router.get("/category/{category}")
def get_matches_by_category(category: str, limit: int = 50, db: Session = Depends(get_db_session)):
    """
    Fetch recent matches filtered by category.
    Category should be one of: MS, WS, MD, WD, XD
    """
    valid_categories = ["MS", "WS", "MD", "WD", "XD"]
    if category.upper() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}",
        )

    try:
        matches = matches_service.get_matches_by_category(db, category, limit)
        return matches if matches else []

    except Exception as e:
        logger.error(f"Error fetching matches by category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch matches",
        )


@router.get("/recent")
def get_recent_matches(limit: int = 20, db: Session = Depends(get_db_session)):
    """
    Fetch most recent matches across all tournaments.
    """
    try:
        matches = matches_service.get_recent_matches(db, limit)
        return matches if matches else []

    except Exception as e:
        logger.error(f"Error fetching recent matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent matches",
        )


# ============================================================================
# MATCH STATISTICS
# ============================================================================


@router.get("/stats/player/{player_id}")
def get_player_match_stats(player_id: int, db: Session = Depends(get_db_session)):
    """
    Get match statistics for a specific player.
    Includes singles and doubles records.
    """
    try:
        stats = matches_service.get_player_match_stats(db, player_id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found",
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player match stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch player statistics",
        )


@router.get("/stats/head-to-head")
def get_head_to_head_stats(player1_id: int, player2_id: int, db: Session = Depends(get_db_session)):
    """
    Get head-to-head statistics between two players.
    """
    try:
        stats = matches_service.get_head_to_head_stats(db, player1_id, player2_id)
        return stats

    except Exception as e:
        logger.error(f"Error fetching head-to-head stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch head-to-head statistics",
        )
