# ============================================================================
# FILE: app/routes/coaches.py
# REFACTORED VERSION - Service layer integration
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /coaches                    - List all coaches
# GET  /coaches/{slug}             - Get coach details by slug
# GET  /coaches/{slug}/stats       - Get coach statistics

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.schemas import CoachWithClub, CoachList
from app.services import coaches_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/coaches", tags=["Coaches"])


@router.get("", response_model=List[CoachList])
def get_all_coaches(db: Session = Depends(get_db_session)):
    """
    Fetch all coaches for dashboard navbar dropdown.
    Returns minimal coach information sorted alphabetically by last name.
    """
    try:
        coaches = coaches_service.get_all_coaches(db)
        return coaches if coaches else []

    except Exception as e:
        logger.error(f"Error fetching coaches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch coaches",
        )


@router.get("/{slug}", response_model=CoachWithClub)
def get_coach_by_slug(slug: str, db: Session = Depends(get_db_session)):
    """
    Fetch detailed information for a specific coach by slug.
    Includes club information and certification details.
    """
    try:
        coach = coaches_service.get_coach_by_slug(db, slug)

        if not coach:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coach with slug '{slug}' not found",
            )

        return coach

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching coach by slug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch coach",
        )


@router.get("/{slug}/stats")
def get_coach_stats(slug: str, db: Session = Depends(get_db_session)):
    """
    Fetch statistics for a coach including tournament participation.
    """
    try:
        stats = coaches_service.get_coach_stats(db, slug)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coach with slug '{slug}' not found",
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching coach stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch coach statistics",
        )
