# ============================================================================
# FILE: app/routes/rankings.py
# Rankings API Endpoints
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# GET  /rankings/global                        - Get global player rankings
# GET  /rankings/category/{category}           - Rankings for a specific category
# GET  /rankings/player/{player_slug}          - Get ranking for a specific player
# GET  /rankings/player/{player_slug}/history  - Player ranking history
# GET  /rankings/tournament/{tournament_slug}  - Rankings for a tournament
# POST /rankings/calculate/{tournament_id}     - Calculate rankings for a tournament
# POST /rankings/recalculate/all               - Recalculate all rankings
# GET  /rankings/top-players                   - Get top players across categories

from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db_session
from app.services.ranking_calculator import calculate_rankings_for_tournament

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rankings", tags=["Rankings"])


# ============================================================================
# GLOBAL RANKINGS
# ============================================================================


@router.get("/global")
def get_global_rankings(
    category: Optional[str] = Query(
        None, description="Filter by category: MS, WS, MD, WD, XD"
    ),
    limit: int = Query(50, ge=1, le=200, description="Number of players to return"),
    db: Session = Depends(get_db_session),
):
    """
    Get global player rankings across all tournaments.
    """
    try:
        if category:
            query = text(
                """
                SELECT 
                    pr.player_id,
                    pr.category,
                    pr.current_rank as rank,
                    pr.previous_rank,
                    pr.total_points as points,
                    pr.tournament_points,
                    pr.match_points,
                    pr.set_points,
                    pr.tournaments_played,
                    pr.matches_won,
                    pr.matches_lost,
                    pr.sets_won,
                    pr.sets_lost,
                    pr.peak_rank,
                    pr.peak_rank_date,
                    CONCAT(p.first_name, ' ', p.last_name) as player_name,
                    p.first_name,
                    p.last_name,
                    p.gender,
                    p.image_url,
                    p.slug,
                    c.name as club_name,
                    c.logo_url as club_logo,
                    CASE 
                        WHEN pr.previous_rank IS NULL THEN 'new'
                        WHEN pr.current_rank < pr.previous_rank THEN 'up'
                        WHEN pr.current_rank > pr.previous_rank THEN 'down'
                        ELSE 'same'
                    END as rank_change,
                    CASE 
                        WHEN (pr.matches_won + pr.matches_lost) > 0 
                        THEN ROUND((pr.matches_won::DECIMAL / (pr.matches_won + pr.matches_lost) * 100), 1)
                        ELSE 0
                    END as win_percentage
                FROM player_rankings pr
                JOIN players p ON pr.player_id = p.id
                LEFT JOIN clubs c ON p.club_id = c.id
                WHERE pr.category = :category
                ORDER BY pr.category, pr.current_rank
                LIMIT :limit
                """
            )
            params = {"category": category.upper(), "limit": limit}
        else:
            query = text(
                """
                SELECT 
                    pr.player_id,
                    pr.category,
                    pr.current_rank as rank,
                    pr.previous_rank,
                    pr.total_points as points,
                    pr.tournament_points,
                    pr.match_points,
                    pr.set_points,
                    pr.tournaments_played,
                    pr.matches_won,
                    pr.matches_lost,
                    pr.sets_won,
                    pr.sets_lost,
                    pr.peak_rank,
                    pr.peak_rank_date,
                    CONCAT(p.first_name, ' ', p.last_name) as player_name,
                    p.first_name,
                    p.last_name,
                    p.gender,
                    p.image_url,
                    p.slug,
                    c.name as club_name,
                    c.logo_url as club_logo,
                    CASE 
                        WHEN pr.previous_rank IS NULL THEN 'new'
                        WHEN pr.current_rank < pr.previous_rank THEN 'up'
                        WHEN pr.current_rank > pr.previous_rank THEN 'down'
                        ELSE 'same'
                    END as rank_change,
                    CASE 
                        WHEN (pr.matches_won + pr.matches_lost) > 0 
                        THEN ROUND((pr.matches_won::DECIMAL / (pr.matches_won + pr.matches_lost) * 100), 1)
                        ELSE 0
                    END as win_percentage
                FROM player_rankings pr
                JOIN players p ON pr.player_id = p.id
                LEFT JOIN clubs c ON p.club_id = c.id
                ORDER BY pr.category, pr.current_rank
                LIMIT :limit
                """
            )
            params = {"limit": limit}

        res = db.execute(query, params)
        rankings = [dict(r) for r in res.mappings().all()]

        if not rankings:
            return {"rankings": [], "total": 0}

        if not category:
            grouped: dict[str, list[dict]] = {}
            for rank in rankings:
                cat = rank["category"]
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(rank)

            return {"rankings": grouped, "total": len(rankings)}

        return {"category": category.upper(), "rankings": rankings, "total": len(rankings)}

    except Exception as e:
        logger.error(f"Error fetching global rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rankings",
        )


@router.get("/category/{category}")
def get_category_rankings(category: str, limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db_session)):
    """
    Get rankings for a specific category.
    """
    valid_categories = ["MS", "WS", "MD", "WD", "XD"]
    category_upper = category.upper()

    if category_upper not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}",
        )

    return get_global_rankings(category=category_upper, limit=limit, db=db)


# ============================================================================
# PLAYER-SPECIFIC RANKINGS
# ============================================================================


@router.get("/player/{player_slug}")
def get_player_rankings(player_slug: str, db: Session = Depends(get_db_session)):
    """
    Get complete ranking information for a specific player across all categories.
    """
    try:
        r = db.execute(
            text(
                """
                SELECT id, first_name, last_name, image_url, slug
                FROM players
                WHERE LOWER(slug) = LOWER(:slug)
                    AND deleted_at IS NULL
                """
            ),
            {"slug": player_slug},
        )

        player = r.mappings().first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        r2 = db.execute(
            text(
                """
                SELECT 
                    pr.category,
                    pr.current_rank,
                    pr.previous_rank,
                    pr.total_points,
                    pr.tournament_points,
                    pr.match_points,
                    pr.set_points,
                    pr.tournaments_played,
                    pr.matches_won,
                    pr.matches_lost,
                    pr.sets_won,
                    pr.sets_lost,
                    pr.peak_rank,
                    pr.peak_rank_date,
                    pr.last_updated,
                    CASE 
                        WHEN pr.previous_rank IS NULL THEN 'new'
                        WHEN pr.current_rank < pr.previous_rank THEN 'up'
                        WHEN pr.current_rank > pr.previous_rank THEN 'down'
                        ELSE 'same'
                    END as rank_change,
                    CASE 
                        WHEN (pr.matches_won + pr.matches_lost) > 0 
                        THEN ROUND((pr.matches_won::DECIMAL / (pr.matches_won + pr.matches_lost) * 100), 1)
                        ELSE 0
                    END as win_percentage
                FROM player_rankings pr
                WHERE pr.player_id = :player_id
                ORDER BY pr.category
                """
            ),
            {"player_id": player["id"]},
        )

        categories = [dict(r) for r in r2.mappings().all()]

        return {
            "player": {
                "id": player["id"],
                "name": f"{player['first_name']} {player['last_name']}",
                "first_name": player["first_name"],
                "last_name": player["last_name"],
                "image_url": player["image_url"],
                "slug": player["slug"],
            },
            "rankings": categories if categories else [],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch player rankings",
        )


@router.get("/player/{player_slug}/history")
def get_player_ranking_history(
    player_slug: str,
    category: Optional[str] = None,
    days: int = Query(90, ge=7, le=365, description="Number of days of history"),
    db: Session = Depends(get_db_session),
):
    """
    Get ranking history for a player to show rank progression over time.
    """
    try:
        r = db.execute(
            text(
                """
                SELECT id FROM players
                WHERE LOWER(slug) = LOWER(:slug) AND deleted_at IS NULL
                """
            ),
            {"slug": player_slug},
        )

        player = r.mappings().first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        if category:
            query = text(
                """
                SELECT 
                    rh.category,
                    rh.rank,
                    rh.total_points,
                    rh.recorded_at as date
                FROM ranking_history rh
                WHERE rh.player_id = :player_id
                    AND rh.recorded_at >= CURRENT_DATE - INTERVAL :days || ' days'
                    AND rh.category = :category
                ORDER BY rh.recorded_at ASC, rh.category
                """
            )
            params = {"player_id": player["id"], "days": days, "category": category.upper()}
        else:
            query = text(
                """
                SELECT 
                    rh.category,
                    rh.rank,
                    rh.total_points,
                    rh.recorded_at as date
                FROM ranking_history rh
                WHERE rh.player_id = :player_id
                    AND rh.recorded_at >= CURRENT_DATE - INTERVAL :days || ' days'
                ORDER BY rh.recorded_at ASC, rh.category
                """
            )
            params = {"player_id": player["id"], "days": days}

        r2 = db.execute(query, params)
        history = [dict(rr) for rr in r2.mappings().all()]

        grouped: dict[str, list[dict]] = {}
        for record in history:
            cat = record["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append({
                "date": str(record["date"]),
                "rank": record["rank"],
                "points": record["total_points"],
            })

        return {"player_id": player["id"], "history": grouped, "days": days}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ranking history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ranking history",
        )


# ============================================================================
# TOURNAMENT-SPECIFIC RANKINGS
# ============================================================================


@router.get("/tournament/{tournament_slug}")
def get_tournament_rankings(tournament_slug: str, category: Optional[str] = None, db: Session = Depends(get_db_session)):
    """
    Get player rankings/leaderboard for a specific tournament.
    Shows how players performed in THIS tournament.
    """
    try:
        r = db.execute(
            text(
                """
                SELECT id, name FROM tournaments
                WHERE LOWER(slug) = LOWER(:slug) AND deleted_at IS NULL
                """
            ),
            {"slug": tournament_slug},
        )

        tournament = r.mappings().first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        if category:
            query = text(
                """
                SELECT 
                    tpp.player_id,
                    tpp.category,
                    tpp.total_points,
                    tpp.placement_points,
                    tpp.match_win_points,
                    tpp.set_win_points,
                    tpp.matches_played,
                    tpp.matches_won,
                    tpp.sets_won,
                    tpp.sets_lost,
                    tpp.final_placement,
                    CONCAT(p.first_name, ' ', p.last_name) as player_name,
                    p.first_name,
                    p.last_name,
                    p.image_url,
                    p.slug,
                    c.name as club_name,
                    c.logo_url as club_logo,
                    CASE 
                        WHEN tpp.matches_played > 0 
                        THEN ROUND((tpp.matches_won::DECIMAL / tpp.matches_played * 100), 1)
                        ELSE 0
                    END as win_percentage,
                    RANK() OVER (PARTITION BY tpp.category ORDER BY tpp.total_points DESC) as tournament_rank
                FROM tournament_player_points tpp
                JOIN players p ON tpp.player_id = p.id
                LEFT JOIN clubs c ON p.club_id = c.id
                WHERE tpp.tournament_id = :t_id
                    AND tpp.category = :category
                ORDER BY tpp.category, tpp.total_points DESC
                """
            )
            params = {"t_id": tournament["id"], "category": category.upper()}
        else:
            query = text(
                """
                SELECT 
                    tpp.player_id,
                    tpp.category,
                    tpp.total_points,
                    tpp.placement_points,
                    tpp.match_win_points,
                    tpp.set_win_points,
                    tpp.matches_played,
                    tpp.matches_won,
                    tpp.sets_won,
                    tpp.sets_lost,
                    tpp.final_placement,
                    CONCAT(p.first_name, ' ', p.last_name) as player_name,
                    p.first_name,
                    p.last_name,
                    p.image_url,
                    p.slug,
                    c.name as club_name,
                    c.logo_url as club_logo,
                    CASE 
                        WHEN tpp.matches_played > 0 
                        THEN ROUND((tpp.matches_won::DECIMAL / tpp.matches_played * 100), 1)
                        ELSE 0
                    END as win_percentage,
                    RANK() OVER (PARTITION BY tpp.category ORDER BY tpp.total_points DESC) as tournament_rank
                FROM tournament_player_points tpp
                JOIN players p ON tpp.player_id = p.id
                LEFT JOIN clubs c ON p.club_id = c.id
                WHERE tpp.tournament_id = :t_id
                ORDER BY tpp.category, tpp.total_points DESC
                """
            )
            params = {"t_id": tournament["id"]}

        res = db.execute(query, params)
        rankings = [dict(r) for r in res.mappings().all()]

        if not rankings:
            return {
                "tournament": {
                    "id": tournament["id"],
                    "name": tournament["name"],
                    "slug": tournament_slug,
                },
                "rankings": [],
                "total": 0,
            }

        if not category:
            grouped: dict[str, list[dict]] = {}
            for rank in rankings:
                cat = rank["category"]
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(rank)

            return {
                "tournament": {
                    "id": tournament["id"],
                    "name": tournament["name"],
                    "slug": tournament_slug,
                },
                "rankings": grouped,
                "total": len(rankings),
            }

        return {
            "tournament": {
                "id": tournament["id"],
                "name": tournament["name"],
                "slug": tournament_slug,
            },
            "category": category.upper(),
            "rankings": rankings,
            "total": len(rankings),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tournament rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tournament rankings",
        )


# ============================================================================
# ADMIN: CALCULATE RANKINGS
# ============================================================================


@router.post("/calculate/{tournament_id}")
def calculate_tournament_rankings(tournament_id: int):
    """
    ADMIN ENDPOINT: Calculate and update rankings for a tournament.

    This should be called after a tournament is completed.
    It will:
    1. Calculate points for all players
    2. Update tournament_player_points
    3. Update global player_rankings
    4. Update rank positions
    5. Record ranking history
    """
    try:
        logger.info(f"Starting ranking calculation for tournament {tournament_id}")

        result = calculate_rankings_for_tournament(tournament_id)

        return {
            "success": True,
            "tournament_id": tournament_id,
            "players_updated": len(result),
            "message": f"Successfully calculated rankings for {len(result)} players",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate rankings: {str(e)}",
        )


@router.post("/recalculate/all")
def recalculate_all_rankings(db: Session = Depends(get_db_session)):
    """
    ADMIN ENDPOINT: Recalculate rankings for ALL tournaments.
    Use this to rebuild the entire ranking system from scratch.

    WARNING: This may take a while for many tournaments.
    """
    try:
        r = db.execute(
            text(
                """
                SELECT id, name 
                FROM tournaments 
                WHERE deleted_at IS NULL 
                ORDER BY start_date ASC, id ASC
                """
            )
        )

        tournaments = [dict(row) for row in r.mappings().all()]

        if not tournaments:
            return {
                "success": True,
                "tournaments_processed": 0,
                "message": "No tournaments found",
            }

        results = []
        for tournament in tournaments:
            try:
                logger.info(f"Calculating rankings for: {tournament['name']}")
                calculate_rankings_for_tournament(tournament["id"])
                results.append(
                    {
                        "tournament_id": tournament["id"],
                        "name": tournament["name"],
                        "status": "success",
                    }
                )
            except Exception as e:
                logger.error(f"Error processing tournament {tournament['id']}: {e}")
                results.append(
                    {
                        "tournament_id": tournament["id"],
                        "name": tournament["name"],
                        "status": "failed",
                        "error": str(e),
                    }
                )

        successful = len([r for r in results if r["status"] == "success"])

        return {
            "success": True,
            "tournaments_processed": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "details": results,
        }

    except Exception as e:
        logger.error(f"Error recalculating all rankings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recalculate rankings: {str(e)}",
        )


# ============================================================================
# LEADERBOARDS & TOP PLAYERS
# ============================================================================


@router.get("/top-players")
def get_top_players(
    category: Optional[str] = None, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db_session)
):
    """
    Get top players across all categories or specific category.
    Simplified endpoint for homepage/widgets.
    """
    try:
        if category:
            query = text(
                """
                SELECT 
                    pr.current_rank as rank,
                    pr.category,
                    pr.total_points as points,
                    CONCAT(p.first_name, ' ', p.last_name) as name,
                    p.image_url,
                    p.slug,
                    c.name as club,
                    c.logo_url as club_logo,
                    CASE 
                        WHEN pr.previous_rank IS NULL THEN 'same'
                        WHEN pr.current_rank < pr.previous_rank THEN 'up'
                        WHEN pr.current_rank > pr.previous_rank THEN 'down'
                        ELSE 'same'
                    END as change
                FROM player_rankings pr
                JOIN players p ON pr.player_id = p.id
                LEFT JOIN clubs c ON p.club_id = c.id
                WHERE pr.category = :category
                ORDER BY pr.category, pr.current_rank
                LIMIT :limit
                """
            )
            params = {"category": category.upper(), "limit": limit}
        else:
            query = text(
                """
                SELECT 
                    pr.current_rank as rank,
                    pr.category,
                    pr.total_points as points,
                    CONCAT(p.first_name, ' ', p.last_name) as name,
                    p.image_url,
                    p.slug,
                    c.name as club,
                    c.logo_url as club_logo,
                    CASE 
                        WHEN pr.previous_rank IS NULL THEN 'same'
                        WHEN pr.current_rank < pr.previous_rank THEN 'up'
                        WHEN pr.current_rank > pr.previous_rank THEN 'down'
                        ELSE 'same'
                    END as change
                FROM player_rankings pr
                JOIN players p ON pr.player_id = p.id
                LEFT JOIN clubs c ON p.club_id = c.id
                ORDER BY pr.category, pr.current_rank
                LIMIT :limit
                """
            )
            params = {"limit": limit}

        res = db.execute(query, params)
        players = [dict(r) for r in res.mappings().all()]

        return players if players else []

    except Exception as e:
        logger.error(f"Error fetching top players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch top players",
        )
