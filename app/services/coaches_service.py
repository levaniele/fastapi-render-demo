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
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_all_coaches(db: Session):
    """
    Fetch all coaches for dashboard navbar dropdown.
    Returns: List[CoachList] - id, first_name, last_name, image_url, slug
    """
    try:
        res = db.execute(
            text(
                """
                SELECT 
                    id,
                    first_name, 
                    last_name, 
                    image_url,
                    slug
                FROM coaches 
                WHERE deleted_at IS NULL
                ORDER BY last_name ASC, first_name ASC
                """
            )
        )

        coaches = [dict(r) for r in res.mappings().all()]
        return coaches if coaches else []

    except Exception as e:
        logger.error(f"Error fetching coaches: {e}")
        raise


def get_coach_by_slug(db: Session, slug: str):
    """
    Fetch detailed information for a specific coach by slug.
    Includes club information and certification details.
    Returns: CoachWithClub
    """
    try:
        r = db.execute(
            text(
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
                WHERE LOWER(co.slug) = LOWER(:slug)
                    AND co.deleted_at IS NULL
                """
            ),
            {"slug": slug},
        )

        coach = r.mappings().first()
        return dict(coach) if coach else None

    except Exception as e:
        logger.error(f"Error fetching coach by slug: {e}")
        raise


def get_coach_stats(db: Session, slug: str):
    """
    Fetch statistics for a coach including tournament participation.
    Returns: dict with tournament_count and recent_tournaments
    """
    try:
        # Get coach ID
        r = db.execute(
            text(
                """
                SELECT id FROM coaches 
                WHERE LOWER(slug) = LOWER(:slug)
                    AND deleted_at IS NULL
                """
            ),
            {"slug": slug},
        )

        coach = r.mappings().first()

        if not coach:
            return None

        coach_id = coach["id"]

        # Get tournament count
        r2 = db.execute(
            text(
                """
                SELECT COUNT(DISTINCT tournament_id) as tournament_count
                FROM tournament_coaches
                WHERE coach_id = :coach_id
                """
            ),
            {"coach_id": coach_id},
        )

        stats = r2.mappings().first()

        # Get recent tournaments
        r3 = db.execute(
            text(
                """
                SELECT 
                    t.name,
                    t.slug,
                    t.start_date,
                    tc.assigned_role
                FROM tournament_coaches tc
                JOIN tournaments t ON tc.tournament_id = t.id
                WHERE tc.coach_id = :coach_id
                    AND t.deleted_at IS NULL
                ORDER BY t.start_date DESC
                LIMIT 5
                """
            ),
            {"coach_id": coach_id},
        )

        tournaments = [dict(rr) for rr in r3.mappings().all()]

        return {
            "tournament_count": stats["tournament_count"],
            "recent_tournaments": tournaments if tournaments else [],
        }

    except Exception as e:
        logger.error(f"Error fetching coach stats: {e}")
        raise
