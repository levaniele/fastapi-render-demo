"""
Services for Coach operations
All database queries for coach-related endpoints
"""

# ============================================================================
# SUMMARY OF SERVICE (COACHES):
# ============================================================================
# get_all_coaches(db)           - List coaches
# get_coach_by_slug(db, slug)   - Get coach details by slug
# get_coach_stats(db, slug)     - Get stats for coach (tournaments, assignments)
# Used by: /coaches endpoints

import logging
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_all_coaches(db):
    """
    Fetch all coaches for dashboard navbar dropdown.
    Returns: List[CoachList] - id, first_name, last_name, image_url, slug
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT 
                id,
                first_name, 
                last_name, 
                image_url,
                slug
            FROM coaches 
            WHERE deleted_at IS NULL
            ORDER BY last_name ASC, first_name ASC
        """)

        coaches = cur.fetchall()
        return coaches if coaches else []

    except Exception as e:
        logger.error(f"Error fetching coaches: {e}")
        raise
    finally:
        cur.close()


def get_coach_by_slug(db, slug: str):
    """
    Fetch detailed information for a specific coach by slug.
    Includes club information and certification details.
    Returns: CoachWithClub
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT 
                co.id,
                co.first_name, 
                co.last_name, 
                co.certification_level,
                co.certification_level_id,
                co.club_id,
                co.image_url,
                co.slug,
                co.created_at,
                c.name as club_name,
                c.logo_url as club_logo,
                cl.level_name as certification_name
            FROM coaches co
            LEFT JOIN clubs c ON co.club_id = c.id
            LEFT JOIN certification_levels cl ON co.certification_level_id = cl.id
            WHERE LOWER(co.slug) = LOWER(%s)
                AND co.deleted_at IS NULL
        """,
            (slug,),
        )

        coach = cur.fetchone()
        return coach

    except Exception as e:
        logger.error(f"Error fetching coach by slug: {e}")
        raise
    finally:
        cur.close()


def get_coach_stats(db, slug: str):
    """
    Fetch statistics for a coach including tournament participation.
    Returns: dict with tournament_count and recent_tournaments
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        # Get coach ID
        cur.execute(
            """
            SELECT id FROM coaches 
            WHERE LOWER(slug) = LOWER(%s)
                AND deleted_at IS NULL
        """,
            (slug,),
        )

        coach = cur.fetchone()

        if not coach:
            return None

        coach_id = coach["id"]

        # Get tournament count
        cur.execute(
            """
            SELECT COUNT(DISTINCT tournament_id) as tournament_count
            FROM tournament_coaches
            WHERE coach_id = %s
        """,
            (coach_id,),
        )

        stats = cur.fetchone()

        # Get recent tournaments
        cur.execute(
            """
            SELECT 
                t.name,
                t.slug,
                t.start_date,
                tc.assigned_role
            FROM tournament_coaches tc
            JOIN tournaments t ON tc.tournament_id = t.id
            WHERE tc.coach_id = %s
                AND t.deleted_at IS NULL
            ORDER BY t.start_date DESC
            LIMIT 5
        """,
            (coach_id,),
        )

        tournaments = cur.fetchall()

        return {
            "tournament_count": stats["tournament_count"],
            "recent_tournaments": tournaments if tournaments else [],
        }

    except Exception as e:
        logger.error(f"Error fetching coach stats: {e}")
        raise
    finally:
        cur.close()
