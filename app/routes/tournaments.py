# ============================================================================
# FILE: app/routes/tournaments.py
# REFACTORED VERSION - Service layer integration
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /tournaments                                 - List tournaments
# GET  /tournaments/search                          - Search tournaments
# GET  /tournaments/winners                         - List tournament winners
# POST /tournaments/winners                         - Create tournament winners
# PUT  /tournaments/winners/{tournament_id}        - Update tournament winners
# GET  /tournaments/{slug}                          - Tournament details
# GET  /tournaments/{slug}/stats                    - Tournament statistics
# GET  /tournaments/{slug}/matches                  - Tournament matches
# GET  /tournaments/{slug}/standings                - Tournament standings
# GET  /tournaments/{slug}/teams                    - Tournament teams/roster
# GET  /tournaments/{slug}/players                  - Tournament players
# GET  /tournaments/{slug}/staff                    - Tournament staff
# GET  /tournaments/{slug}/matches/{match_id}/rallies - Match rallies
# POST /admin/tournaments                           - Create a tournament (admin)
# PUT  /tournaments/{tournament_id}                - Update a tournament
# PATCH /tournaments/{tournament_id}               - Partial update
# DELETE /tournaments/{tournament_id}              - Delete a tournament

from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session
from app.database import get_db, get_db_session
from app.schemas import (
    TournamentResponse,
    TournamentList,
    TournamentStats,
    TeamRoster,
    TournamentWinnersResponse,
    TournamentWinnersCreate,
    TournamentWinnersUpdate,
    TournamentCreate,
    TournamentUpdate,
)
from app.services import tournaments_service
from app.services.tournaments_service import TournamentService
from app.routes.models import Tournament

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


# ============================================================================
# TOURNAMENT LISTING & SEARCH
# ============================================================================


@router.get("", response_model=List[TournamentList])
def get_all_tournaments(db=Depends(get_db)):
    """Fetch all tournaments with metadata for UI cards."""
    try:
        tournaments = tournaments_service.get_all_tournaments(db)
        return tournaments if tournaments else []

    except Exception as e:
        logger.error(f"Error fetching tournaments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournaments",
        )


@router.get("/search")
def search_tournaments(query: str, db=Depends(get_db)):
    """Search tournaments by name or location."""
    try:
        results = tournaments_service.search_tournaments(db, query)
        return results if results else []

    except Exception as e:
        logger.error(f"Error searching tournaments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed"
        )


@router.get("/winners", response_model=List[TournamentWinnersResponse])
def get_tournament_winners(slug: Optional[str] = None, db=Depends(get_db)):
    """Fetch tournament winners (clubs and/or players)."""
    try:
        winners = tournaments_service.get_tournament_winners(db, slug)
        return winners if winners else []

    except Exception as e:
        logger.error(f"Error fetching tournament winners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament winners",
        )


@router.post("/winners", response_model=TournamentWinnersResponse)
def create_tournament_winners(
    payload: TournamentWinnersCreate, db=Depends(get_db)
):
    """Create winners for a tournament (upsert)."""
    try:
        winners = tournaments_service.upsert_tournament_winners(
            db=db,
            tournament_id=payload.tournament_id,
            first_place_club_id=payload.first_place_club_id,
            second_place_club_id=payload.second_place_club_id,
            third_place_club_id=payload.third_place_club_id,
            first_place_player_id=payload.first_place_player_id,
            second_place_player_id=payload.second_place_player_id,
            third_place_player_id=payload.third_place_player_id,
        )
        return winners

    except Exception as e:
        logger.error(f"Error creating tournament winners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tournament winners",
        )


@router.put("/winners/{tournament_id}", response_model=TournamentWinnersResponse)
def update_tournament_winners(
    tournament_id: int, payload: TournamentWinnersUpdate, db=Depends(get_db)
):
    """Update winners for a tournament (upsert)."""
    try:
        winners = tournaments_service.upsert_tournament_winners(
            db=db,
            tournament_id=tournament_id,
            first_place_club_id=payload.first_place_club_id,
            second_place_club_id=payload.second_place_club_id,
            third_place_club_id=payload.third_place_club_id,
            first_place_player_id=payload.first_place_player_id,
            second_place_player_id=payload.second_place_player_id,
            third_place_player_id=payload.third_place_player_id,
        )
        return winners

    except Exception as e:
        logger.error(f"Error updating tournament winners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tournament winners",
        )


# ============================================================================
# TOURNAMENT DETAILS & OVERVIEW
# ============================================================================


@router.get("/{slug}", response_model=TournamentResponse)
def get_tournament_by_slug(slug: str, db=Depends(get_db)):
    """Fetch basic tournament information by slug."""
    try:
        tournament = tournaments_service.get_tournament_by_slug(db, slug)

        if not tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with slug '{slug}' not found",
            )

        return tournament

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament",
        )


@router.get("/{slug}/stats", response_model=TournamentStats)
def get_tournament_stats(slug: str, db=Depends(get_db)):
    """Fetch comprehensive tournament statistics."""
    try:
        stats = tournaments_service.get_tournament_stats(db, slug)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with slug '{slug}' not found",
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tournament stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament statistics",
        )


# ============================================================================
# MATCHES & RESULTS
# ============================================================================


@router.get("/{slug}/matches")
def get_tournament_matches(slug: str, db=Depends(get_db)):
    """Fetch all match ties for a tournament with individual match details."""
    try:
        matches = tournaments_service.get_tournament_matches(db, slug)

        if matches is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with slug '{slug}' not found",
            )

        return matches

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tournament matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch matches",
        )


# ============================================================================
# STANDINGS
# ============================================================================


@router.get("/{slug}/standings")
def get_tournament_standings(
    slug: str, group_name: Optional[str] = None, db=Depends(get_db)
):
    """
    Calculate tournament standings with head-to-head records.
    If group_name is provided, filter by that group.
    """
    try:
        standings = tournaments_service.get_tournament_standings(db, slug, group_name)

        if standings is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with slug '{slug}' not found",
            )

        return standings

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating standings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate standings",
        )


# ============================================================================
# TEAMS & ROSTERS
# ============================================================================


@router.get("/{slug}/teams", response_model=List[TeamRoster])
def get_tournament_teams(slug: str, db=Depends(get_db)):
    """
    Fetch team rosters showing which players each club registered.
    Uses tournament_lineups table.
    """
    try:
        teams = tournaments_service.get_tournament_teams(db, slug)
        return teams if teams else []

    except Exception as e:
        logger.error(f"Error fetching tournament teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament teams",
        )


# ============================================================================
# PLAYERS & LINEUPS
# ============================================================================


@router.get("/{slug}/players")
def get_tournament_players(slug: str, db=Depends(get_db)):
    """Fetch all players participating in a tournament WITH their categories."""
    try:
        players = tournaments_service.get_tournament_players(db, slug)
        return players if players else []

    except Exception as e:
        logger.error(f"Error fetching tournament players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament players",
        )


@router.get("/{slug}/staff")
def get_tournament_staff(slug: str, db=Depends(get_db)):
    """
    Fetch all staff (coaches and umpires) assigned to a tournament.
    Uses tournament_coaches and tournament_umpires tables.
    """
    try:
        staff = tournaments_service.get_tournament_staff(db, slug)

        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with slug '{slug}' not found",
            )

        return staff

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tournament staff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament staff",
        )


@router.get("/{slug}/matches/{match_id}/rallies")
def get_match_rallies(slug: str, match_id: int, db=Depends(get_db)):
    """
    Fetch rallies for a match.
    Matches URL: /tournaments/{slug}/matches/{match_id}/rallies
    """
    try:
        # We pass 'db' and 'match_id' to the service
        rallies = tournaments_service.get_match_rallies(db, match_id)
        return rallies if rallies else []

    except Exception as e:
        logger.error(f"Error fetching match rallies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch match rallies",
        )


# ============================================================================
# ADMIN ENDPOINTS - Create, Update, Delete
# ============================================================================


@router.post(
    "/admin/tournaments",
    response_model=TournamentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tournament(
    tournament_data: TournamentCreate,
    response: Response,
    db: Session = Depends(get_db_session),
):
    """Create a new tournament. If a tournament with the same slug exists,
    perform an update instead of returning a conflict.
    """
    try:
        # If slug already exists, update instead of creating (idempotent for UI)
        existing = (
            db.query(Tournament).filter(Tournament.slug == tournament_data.slug).first()
        )
        logger.debug(
            f"Create: existing tournament lookup for slug '{tournament_data.slug}': {existing}"
        )
        if existing:
            logger.info(f"Slug exists, updating tournament id {existing.id}")
            # Convert TournamentCreate to TournamentUpdate for the update call
            update_data = TournamentUpdate(
                **tournament_data.model_dump(exclude_unset=True)
            )
            updated = TournamentService.update_tournament(
                db=db, tournament_id=int(existing.id), tournament_data=update_data
            )
            # When updating via POST we must return 200 OK (not 201 Created)
            response.status_code = status.HTTP_200_OK
            return updated

        new_tournament = TournamentService.create_tournament(
            db=db, tournament_data=tournament_data
        )
        return new_tournament

    except ValueError as e:
        # Keep this to surface other create-time conflicts
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tournament",
        )


@router.put("/{tournament_id}", response_model=TournamentResponse)
def update_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    db: Session = Depends(get_db_session),
):
    """Update an existing tournament."""
    try:
        updated_tournament = TournamentService.update_tournament(
            db=db, tournament_id=tournament_id, tournament_data=tournament_data
        )

        if not updated_tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id '{tournament_id}' not found",
            )

        return updated_tournament

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tournament",
        )


@router.patch("/{tournament_id}", response_model=TournamentResponse)
def patch_tournament(
    tournament_id: int,
    tournament_data: TournamentUpdate,
    db: Session = Depends(get_db_session),
):
    """Patch an existing tournament (partial update)."""
    try:
        updated_tournament = TournamentService.update_tournament(
            db=db, tournament_id=tournament_id, tournament_data=tournament_data
        )

        if not updated_tournament:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id '{tournament_id}' not found",
            )

        return updated_tournament

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch tournament",
        )


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(tournament_id: int, db: Session = Depends(get_db_session)):
    """Delete a tournament."""
    try:
        deleted = TournamentService.delete_tournament(
            db=db, tournament_id=tournament_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tournament with id '{tournament_id}' not found",
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tournament: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tournament",
        )
