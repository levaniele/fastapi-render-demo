# ============================================================================
# SUMMARY OF SERVICE (COACHES):
# ============================================================================
# get_all_coaches(db)           - List coaches
# get_coach_by_slug(db, slug)   - Get coach details by slug
# get_coach_stats(db, slug)     - Get stats for coach (tournaments, assignments)

# Used by: /coaches endpoints

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.coach import Coach
from app.models.club import Club
from app.models.certification_level import CertificationLevel
from app.models.tournament import Tournament, TournamentCoach

logger = logging.getLogger(__name__)


def get_all_coaches(db: Session):
    """
    Fetch all coaches for dashboard navbar dropdown.
    Returns: List[CoachList] - id, first_name, last_name, image_url, slug
    """
    try:
        coaches = (
            db.query(
                Coach.id,
                Coach.first_name,
                Coach.last_name,
                Coach.image_url,
                Coach.slug,
            )
            .filter(Coach.deleted_at.is_(None))
            .order_by(Coach.last_name.asc(), Coach.first_name.asc())
            .all()
        )

        return [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "image_url": c.image_url,
                "slug": c.slug,
            }
            for c in coaches
        ]


    except Exception as e:
        logger.error(f"Error fetching coaches: {e}")
        raise


def get_coach_by_slug(db: Session, slug: str):
    try:
        result = (
            db.query(
                Coach.id,
                Coach.first_name,
                Coach.last_name,
                Coach.certification_level,
                Coach.certification_level_id,
                Coach.club_id,
                Coach.image_url,
                Coach.slug,
                Coach.created_at,
                Club.name.label("club_name"),
                Club.logo_url.label("club_logo"),
                CertificationLevel.level_name.label("certification_name"),
            )
            .outerjoin(Club, Coach.club_id == Club.id)
            .outerjoin(CertificationLevel, Coach.certification_level_id == CertificationLevel.id)
            .filter(func.lower(Coach.slug) == slug.lower())
            .filter(Coach.deleted_at.is_(None))
            .first()
        )

        return result._asdict() if result else None

    except Exception as e:
        logger.error(f"Error fetching coach by slug: {e}")
        raise


def get_coach_stats(db: Session, slug: str):
    try:
        # Get coach ID
        coach_id = (
            db.query(Coach.id)
            .filter(func.lower(Coach.slug) == slug.lower())
            .filter(Coach.deleted_at.is_(None))
            .scalar()
        )

        if not coach_id:
            return None

        # Get tournament count
        tournament_count = (
            db.query(func.count(TournamentCoach.tournament_id.distinct()))
            .filter(TournamentCoach.coach_id == coach_id)
            .scalar()
        )

        # Get recent tournaments
        recent_tournaments = (
            db.query(
                Tournament.name,
                Tournament.slug,
                Tournament.start_date,
                TournamentCoach.assigned_role,
            )
            .join(Tournament, TournamentCoach.tournament_id == Tournament.id)
            .filter(TournamentCoach.coach_id == coach_id)
            .filter(Tournament.deleted_at.is_(None))
            .order_by(Tournament.start_date.desc())
            .limit(5)
            .all()
        )

        return {
            "tournament_count": tournament_count,
            "recent_tournaments": [
                {
                    "name": t.name,
                    "slug": t.slug,
                    "start_date": t.start_date,
                    "assigned_role": t.assigned_role,
                }
                for t in recent_tournaments
            ],
        }

    except Exception as e:
        logger.error(f"Error fetching coach stats: {e}")
        raise
