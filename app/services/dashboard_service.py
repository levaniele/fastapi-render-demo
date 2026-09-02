import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.cache import cached

logger = logging.getLogger(__name__)


@cached(category="reference_data")
def get_dashboard_summary(db: Session, limit: int = 5) -> dict[str, Any]:
    """
    Fetch top entities for dashboard highlights in a single cached call.
    """
    try:
        top_players_q = text(
            """
            SELECT
                p.id AS player_id,
                CONCAT(p.first_name, ' ', p.last_name) AS player_name,
                p.slug,
                p.image_url,
                c.name AS club_name,
                pr.category,
                pr.current_rank AS rank,
                pr.total_points AS points
            FROM player_rankings pr
            JOIN players p ON pr.player_id = p.id
            LEFT JOIN clubs c ON p.club_id = c.id
            WHERE p.deleted_at IS NULL
              AND pr.current_rank IS NOT NULL
            ORDER BY pr.current_rank ASC, pr.total_points DESC, pr.player_id ASC
            LIMIT :limit
            """
        )

        top_clubs_q = text(
            """
            SELECT
                c.id AS club_id,
                c.name AS club_name,
                c.slug,
                c.logo_url,
                COUNT(DISTINCT p.id) AS players_count,
                COALESCE(SUM(pr.total_points), 0) AS total_points
            FROM clubs c
            LEFT JOIN players p
                ON p.club_id = c.id
                AND p.deleted_at IS NULL
            LEFT JOIN player_rankings pr
                ON pr.player_id = p.id
            WHERE c.deleted_at IS NULL
            GROUP BY c.id, c.name, c.slug, c.logo_url
            ORDER BY total_points DESC, players_count DESC, c.name ASC
            LIMIT :limit
            """
        )

        top_coaches_q = text(
            """
            SELECT
                co.id AS coach_id,
                CONCAT(co.first_name, ' ', co.last_name) AS coach_name,
                co.slug,
                co.image_url,
                c.name AS club_name,
                COUNT(DISTINCT tc.tournament_id) AS tournaments_count
            FROM coaches co
            LEFT JOIN clubs c ON co.club_id = c.id
            LEFT JOIN tournament_coaches tc ON tc.coach_id = co.id
            WHERE co.deleted_at IS NULL
            GROUP BY co.id, co.first_name, co.last_name, co.slug, co.image_url, c.name
            ORDER BY tournaments_count DESC, coach_name ASC
            LIMIT :limit
            """
        )

        top_players = [dict(r) for r in db.execute(top_players_q, {"limit": limit}).mappings().all()]
        top_clubs = [dict(r) for r in db.execute(top_clubs_q, {"limit": limit}).mappings().all()]
        top_coaches = [dict(r) for r in db.execute(top_coaches_q, {"limit": limit}).mappings().all()]

        return {
            "top_players": top_players,
            "top_clubs": top_clubs,
            "top_coaches": top_coaches,
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}", exc_info=True)
        raise
