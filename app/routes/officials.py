# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /officials/umpires                  - List all umpires
# GET  /officials/umpires/{slug}           - Get umpire details by slug
# GET  /officials/umpires/{slug}/stats     - Get umpire statistics and match history
# GET  /officials/referees                 - List all referees
# GET  /officials/referees/{slug}          - Get referee details by slug

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging
from app.database import get_db
from app.schemas import UmpireResponse, UmpireProfileWithStats, RefereeResponse
from app.services import officials_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/officials", tags=["Technical Officials"])

# --- UMPIRES ENDPOINTS ---


@router.get("/umpires", response_model=List[UmpireResponse])
def get_all_umpires(db=Depends(get_db)):
    """Fetch all active umpires from the database."""
    try:
        umpires = officials_service.get_all_umpires(db)
        return umpires if umpires else []

    except Exception as e:
        logger.error(f"Error fetching umpires: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch umpires",
        )


@router.get("/umpires/{slug}", response_model=UmpireResponse)
def get_umpire_by_slug(slug: str, db=Depends(get_db)):
    """Fetch a single umpire profile by their unique slug."""
    try:
        umpire = officials_service.get_umpire_by_slug(db, slug)

        if not umpire:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Umpire not found"
            )

        return umpire

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching umpire details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


@router.get("/umpires/{slug}/stats", response_model=UmpireProfileWithStats)
def get_umpire_statistics(slug: str, db=Depends(get_db)):
    """
    Get full profile of an umpire including:
    - Personal Details
    - List of matches officiated
    - List of tournaments participated in
    """
    try:
        umpire_stats = officials_service.get_umpire_stats_by_slug(db, slug)

        if not umpire_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Umpire not found"
            )

        return umpire_stats

    except HTTPException:
        raise
    except Exception as e:
        # Log the error here if you have a logger configured
        print(f"Error fetching umpire stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# --- REFEREES ENDPOINTS ---


@router.get("/referees", response_model=List[RefereeResponse])
def get_all_referees(db=Depends(get_db)):
    """Fetch all active referees from the database."""
    try:
        referees = officials_service.get_all_referees(db)
        return referees if referees else []

    except Exception as e:
        logger.error(f"Error fetching referees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch referees",
        )


@router.get("/referees/{slug}", response_model=RefereeResponse)
def get_referee_by_slug(slug: str, db=Depends(get_db)):
    """Fetch a single referee profile by their unique slug."""
    try:
        referee = officials_service.get_referee_by_slug(db, slug)

        if not referee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Referee not found"
            )

        return referee

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching referee details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )
