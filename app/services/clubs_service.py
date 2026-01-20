"""
Services for Club operations
All database queries for club-related endpoints
"""

import logging
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_all_clubs(db):
    """
    Fetch all clubs for dashboard and dropdown lists.
    Returns: List[ClubList] - id, name, slug, logo_url
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT id, name, slug, logo_url 
            FROM clubs 
            WHERE deleted_at IS NULL
            ORDER BY name ASC
        """)

        clubs = cur.fetchall()
        return clubs if clubs else []

    except Exception as e:
        logger.error(f"Error fetching clubs: {e}")
        raise
    finally:
        cur.close()


def get_club_by_slug(db, slug: str):
    """
    Fetch club details with head coach information.
    Returns: ClubResponse with joined coach data
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT 
                c.id, c.name, c.slug, c.location, c.logo_url, c.created_at, c.head_coach_id,
                co.first_name as coach_first_name,
                co.last_name as coach_last_name,
                co.image_url as coach_image_url,
                co.slug as coach_slug
            FROM clubs c
            LEFT JOIN coaches co ON c.head_coach_id = co.id
            WHERE LOWER(c.slug) = LOWER(%s) 
            AND c.deleted_at IS NULL
        """,
            (slug,),
        )

        club = cur.fetchone()
        return club

    except Exception as e:
        logger.error(f"Error fetching club: {e}")
        raise
    finally:
        cur.close()


def get_club_players(db, slug: str):
    """
    Fetch all players belonging to a club with their rankings.
    Returns: List of players with aggregated rankings
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
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
            WHERE LOWER(c.slug) = LOWER(%s)
                AND p.deleted_at IS NULL
                AND c.deleted_at IS NULL
            ORDER BY p.last_name ASC
        """,
            (slug,),
        )

        players = cur.fetchall()
        return players if players else []

    except Exception as e:
        logger.error(f"Error fetching club players: {e}")
        raise
    finally:
        cur.close()
