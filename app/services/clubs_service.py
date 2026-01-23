"""
Services for Club operations
All database queries for club-related endpoints
"""

# ============================================================================
# SUMMARY OF SERVICE (CLUBS):
# ============================================================================
# get_all_clubs(db)             - List all clubs
# get_club_by_slug(db, slug)    - Get club details by slug
# get_club_players(db, slug)    - Get players for a club with rankings
# Used by: /clubs endpoints

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_all_clubs(db: Session):
    """
    Fetch all clubs for dashboard and dropdown lists.
    Returns: List[ClubList] - id, name, slug, logo_url
    """
    try:
        from app.models import Club
        
        clubs = db.query(Club.id, Club.name, Club.slug, Club.logo_url).filter(
            Club.deleted_at == None
        ).order_by(Club.name.asc()).all()

        return [
            {
                "id": c.id, 
                "name": c.name, 
                "slug": c.slug, 
                "logo_url": c.logo_url
            } 
            for c in clubs
        ]

    except Exception as e:
        logger.error(f"Error fetching clubs: {e}")
        raise


def get_club_by_slug(db: Session, slug: str):
    """
    Fetch club details with head coach information.
    Returns: ClubResponse with joined coach data
    """
    try:
        # Using text() for join with Coach to avoid need for Coach model if not present,
        # but maximizing ORM feeling where possible isn't easy without the model.
        # Keeping existing efficient query but ensuring safety.
        # Since the goal is migrating from psycopg2 (cursors), and this uses db.execute (SQLAlchemy),
        # it is technically already migrated to SQLAlchemy Core. 
        # I will leave this complex query as is to ensure correctness.
        res = db.execute(
            text(
                """
                SELECT 
                    c.id, c.name, c.slug, c.logo_url, c.created_at, c.head_coach_id,
                    co.first_name as coach_first_name,
                    co.last_name as coach_last_name,
                    co.image_url as coach_image_url,
                    co.slug as coach_slug
                FROM clubs c
                LEFT JOIN coaches co ON c.head_coach_id = co.id
                WHERE LOWER(c.slug) = LOWER(:slug)
                AND c.deleted_at IS NULL
                """
            ),
            {"slug": slug},
        )

        club = res.mappings().first()
        return dict(club) if club else None

    except Exception as e:
        logger.error(f"Error fetching club: {e}")
        raise


def get_club_players(db: Session, slug: str):
    """
    Fetch all players belonging to a club with their rankings.
    Returns: List of players with aggregated rankings
    """
    try:
        res = db.execute(
            text(
                """
                WITH CategoryRankings AS (
                    SELECT 
                        player_id, category, 
                        RANK() OVER (PARTITION BY category ORDER BY total_points DESC, player_id ASC) as c_rank
                    FROM player_rankings
                    WHERE total_points > 0
                ),
                AggregatedRankings AS (
                    SELECT 
                        player_id,
                        jsonb_agg(jsonb_build_object('category', category, 'rank', c_rank)) as rankings
                    FROM CategoryRankings
                    GROUP BY player_id
                )
                SELECT 
                    p.id, p.first_name, p.last_name, p.gender, p.nationality_code, 
                    p.image_url, p.slug,
                    COALESCE(ar.rankings, '[]'::jsonb) as rankings
                FROM players p
                JOIN clubs c ON p.club_id = c.id
                LEFT JOIN AggregatedRankings ar ON p.id = ar.player_id
                WHERE LOWER(c.slug) = LOWER(:slug)
                    AND p.deleted_at IS NULL
                    AND c.deleted_at IS NULL
                ORDER BY p.last_name ASC
                """
            ),
            {"slug": slug},
        )

        players = [dict(r) for r in res.mappings().all()]
        return players if players else []

    except Exception as e:
        logger.error(f"Error fetching club players: {e}")
        raise
