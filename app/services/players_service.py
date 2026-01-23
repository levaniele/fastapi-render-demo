# ============================================================================
# SUMMARY OF SERVICE (PLAYERS) - SQLAlchemy version
# ============================================================================
# get_player_count(db)                 - Health check / player count
# get_all_players_with_clubs(db)       - List players with aggregated rankings
# get_players_by_gender(db, gender)    - Filter players by gender
# get_player_by_slug(db, slug)         - Get player profile by slug
# get_player_stats(db, slug)           - Player stats (wins, participation)
# get_tournament_history(db, slug)     - Player tournament history
# get_player_match_history(db, slug)   - Player match history
# Used by: /players endpoints

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.models import Player

logger = logging.getLogger(__name__)


def get_player_count(db: Session) -> int:
    """Simple test to verify database connection and health using ORM."""
    try:
        count = db.query(func.count(Player.id)).filter(Player.deleted_at == None).scalar()
        logger.info(f"Health check: {count} active players found in database.")
        return int(count or 0)
    except Exception as e:
        logger.error(f"Error during player count health check: {e}", exc_info=True)
        raise


def get_all_players_with_clubs(db: Session) -> list[dict]:
    """List players with aggregated rankings using complex CTE query."""
    try:
        result = db.execute(text("""
            -- 1. Calculate Ranks Dynamically (Avoids 'rank' keyword issues)
            WITH RankedEntries AS (
                SELECT
                    player_id,
                    category,
                    -- Calculate rank: #1 is highest points
                    RANK() OVER (PARTITION BY category ORDER BY total_points DESC) as calc_rank
                FROM player_rankings
            ),
            -- 2. Aggregate Ranks into JSON Array per Player
            AggregatedRankings AS (
                SELECT
                    player_id,
                    jsonb_agg(
                        jsonb_build_object(
                            'category', category,
                            'rank', calc_rank
                        )
                    ) as rankings
                FROM RankedEntries
                GROUP BY player_id
            )
            -- 3. Main Selection
            SELECT
                p.id,
                p.first_name,
                p.last_name,
                p.gender,
                p.birth_date,
                p.nationality_code,
                p.slug,
                p.image_url,
                p.club_id,
                p.created_at,

                c.name as club_name,
                c.logo_url as club_logo,

                -- Metrics (with defaults)
                COALESCE(p.metric_speed, 85) as metric_speed,
                COALESCE(p.metric_stamina, 78) as metric_stamina,
                COALESCE(p.metric_agility, 92) as metric_agility,
                COALESCE(p.metric_power, 74) as metric_power,

                -- Join the calculated rankings (default to empty list if null)
                COALESCE(ar.rankings, '[]'::jsonb) as rankings

            FROM players p
            LEFT JOIN clubs c ON p.club_id = c.id
            LEFT JOIN AggregatedRankings ar ON p.id = ar.player_id
            WHERE p.deleted_at IS NULL
            ORDER BY p.id ASC
        """))
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error fetching all players: {e}", exc_info=True)
        raise


def get_players_by_gender(db: Session, gender: str) -> list[dict]:
    """Fetches players filtered by gender with consistent rankings array format."""
    try:
        result = db.execute(text("""
            WITH CategoryRankings AS (
                SELECT
                    player_id, category, total_points,
                    RANK() OVER (PARTITION BY category ORDER BY total_points DESC, player_id ASC) as c_rank
                FROM player_rankings
                WHERE total_points > 0
            ),
            AggregatedRankings AS (
                SELECT
                    player_id,
                    jsonb_agg(
                        jsonb_build_object(
                            'category', category,
                            'rank', c_rank
                        )
                    ) as all_ranks
                FROM CategoryRankings
                GROUP BY player_id
            )
            SELECT p.id, p.first_name, p.last_name, p.gender, p.nationality_code,
                   p.image_url, p.slug, c.name as club_name,
                   COALESCE(ar.all_ranks, '[]'::jsonb) as rankings
            FROM players p
            LEFT JOIN clubs c ON p.club_id = c.id
            LEFT JOIN AggregatedRankings ar ON p.id = ar.player_id
            WHERE p.gender = :gender AND p.deleted_at IS NULL
            ORDER BY p.last_name ASC
        """), {"gender": gender})

        players = [dict(row._mapping) for row in result]
        logger.info(f"Filter: Found {len(players)} players for gender '{gender}'.")
        return players
    except Exception as e:
        logger.error(f"Error filtering players by gender ({gender}): {e}", exc_info=True)
        raise


def get_player_by_slug(db: Session, slug: str) -> dict | None:
    """Fetches a single player's complete profile including full rankings array using ORM for lookup."""
    try:
        player = db.query(Player).filter(func.lower(Player.slug) == slug.lower(), Player.deleted_at == None).first()
        if not player:
            logger.warning(f"Profile Lookup: No player found with slug '{slug}'.")
            return None

        # Fetch club info if present
        club_row = None
        if player.club_id:
            from app.models import Club
            c_obj = db.query(Club).filter(Club.id == player.club_id).first()
            if c_obj:
                club_row = (c_obj.name, c_obj.logo_url)

        # Aggregate rankings for this player
        rank_res = db.execute(text("""
            SELECT COALESCE(jsonb_agg(jsonb_build_object('category', category, 'rank', rnk)), '[]'::jsonb) as rankings
            FROM (
                SELECT category, RANK() OVER (PARTITION BY category ORDER BY total_points DESC, player_id ASC) as rnk
                FROM player_rankings
                WHERE player_id = :p_id
            ) sub
        """), {"p_id": player.id}).fetchone()

        rankings = rank_res[0] if rank_res and rank_res[0] else []

        data = player.to_dict()
        data.update({
            "club_name": club_row[0] if club_row else None,
            "club_logo": club_row[1] if club_row else None,
            "rankings": rankings,
        })
        return data
    except Exception as e:
        logger.error(f"Error fetching player by slug ({slug}): {e}", exc_info=True)
        raise


def get_player_stats(db: Session, slug: str) -> dict | None:
    """Calculates win/loss and tournament participation totals."""
    try:
        # Get player ID
        result = db.execute(text(
            "SELECT id FROM players WHERE LOWER(slug) = LOWER(:slug) AND deleted_at IS NULL"
        ), {"slug": slug})
        player = result.fetchone()

        if not player:
            return None

        p_id = player[0]

        # Singles win/loss logic
        result = db.execute(text("""
            SELECT COUNT(*) as total, SUM(CASE WHEN winner_id = :p_id THEN 1 ELSE 0 END) as wins
            FROM individual_matches
            WHERE match_type = 'singles' AND (player_1_id = :p_id OR player_2_id = :p_id)
        """), {"p_id": p_id})
        singles = dict(result.fetchone()._mapping)

        # Tournament count
        result = db.execute(text("""
            SELECT COUNT(DISTINCT tournament_id) as count
            FROM tournament_lineups
            WHERE player_id = :p_id OR player_2_id = :p_id
        """), {"p_id": p_id})
        tourneys = dict(result.fetchone()._mapping)

        return {
            "singles": {
                "total_matches": singles["total"] or 0,
                "wins": singles["wins"] or 0,
                "losses": (singles["total"] or 0) - (singles["wins"] or 0),
            },
            "tournaments_played": tourneys["count"] or 0,
        }
    except Exception as e:
        logger.error(f"Error calculating stats for player {slug}: {e}", exc_info=True)
        raise


def get_tournament_history(db: Session, slug: str) -> list[dict]:
    """Fetches list of tournaments and points earned."""
    try:
        result = db.execute(text("""
            SELECT t.name, t.start_date as date, t.logo_url, t.slug, tpp.total_points as points_earned,
                   tpp.final_placement as placement, tpp.category
            FROM tournament_player_points tpp
            JOIN tournaments t ON tpp.tournament_id = t.id
            JOIN players p ON tpp.player_id = p.id
            WHERE LOWER(p.slug) = LOWER(:slug) ORDER BY t.start_date DESC
        """), {"slug": slug})
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error fetching history for {slug}: {e}", exc_info=True)
        raise


def get_player_match_history(db: Session, slug: str) -> list[dict]:
    """Fetches last 10 matches with stage and set details."""
    try:
        # Get player ID
        result = db.execute(text(
            "SELECT id FROM players WHERE LOWER(slug) = LOWER(:slug)"
        ), {"slug": slug})
        player = result.fetchone()

        if not player:
            return []

        p_id = player[0]

        result = db.execute(text("""
            SELECT
                im.id, im.category,
                COALESCE(tg.group_name, im.match_type) as stage_name,
                im.set_1_score, im.set_2_score, im.set_3_score,
                im.winner_id,
                p1.id as p1_id, CONCAT(p1.first_name, ' ', p1.last_name) as p1_name,
                p2.id as p2_id, CONCAT(p2.first_name, ' ', p2.last_name) as p2_name,
                :p_id as current_player_id
            FROM individual_matches im
            JOIN players p1 ON im.player_1_id = p1.id
            JOIN players p2 ON im.player_2_id = p2.id
            LEFT JOIN match_ties mt ON im.tie_id = mt.id
            LEFT JOIN tournament_groups tg ON mt.group_id = tg.id
            WHERE im.player_1_id = :p_id OR im.player_2_id = :p_id
            ORDER BY im.id DESC LIMIT 10
        """), {"p_id": p_id})
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"SQL Error in match history: {e}")
        return []
