# ============================================================================
# SUMMARY OF SERVICE (PLAYERS):
# ============================================================================
# get_player_count(conn)                 - Health check / player count
# get_all_players_with_clubs(db)         - List players with aggregated rankings
# get_players_by_gender(conn, gender)    - Filter players by gender
# get_player_by_slug(conn, slug)         - Get player profile by slug
# get_player_stats(conn, slug)           - Player stats (wins, participation)
# Used by: /players endpoints

from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__) 


def get_player_count(conn):
    """Simple test to verify database connection and health."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM players WHERE deleted_at IS NULL;")
            result = cur.fetchone()
            count = list(result.values())[0] if isinstance(result, dict) else result[0]
            logger.info(f"Health check: {count} active players found in database.")
            return count
    except Exception as e:
        logger.error(f"Error during player count health check: {e}", exc_info=True)
        raise


# FILE: app/services/players_service.py


def get_all_players_with_clubs(db):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
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
        """)
        return cur.fetchall()
    finally:
        cur.close()


def get_players_by_gender(conn, gender: str):
    """Fetches players filtered by gender with consistent rankings array format."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
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
                WHERE p.gender = %s AND p.deleted_at IS NULL
                ORDER BY p.last_name ASC;
            """,
                (gender,),
            )
            players = cur.fetchall()
            logger.info(f"Filter: Found {len(players)} players for gender '{gender}'.")
            return players
    except Exception as e:
        logger.error(
            f"Error filtering players by gender ({gender}): {e}", exc_info=True
        )
        raise


def get_player_by_slug(conn, slug: str):
    """Fetches a single player's complete profile including full rankings array."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
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
                SELECT 
                    p.*, 
                    c.name as club_name, 
                    c.logo_url as club_logo,
                    COALESCE(ar.all_ranks, '[]'::jsonb) as rankings
                FROM players p
                LEFT JOIN clubs c ON p.club_id = c.id
                LEFT JOIN AggregatedRankings ar ON p.id = ar.player_id
                WHERE LOWER(p.slug) = LOWER(%s) AND p.deleted_at IS NULL
            """,
                (slug,),
            )
            player = cur.fetchone()
            if not player:
                logger.warning(f"Profile Lookup: No player found with slug '{slug}'.")
            return player
    except Exception as e:
        logger.error(f"Error fetching player by slug ({slug}): {e}", exc_info=True)
        raise


def get_player_stats(conn, slug: str):
    """Calculates win/loss and tournament participation totals."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id FROM players WHERE LOWER(slug) = LOWER(%s) AND deleted_at IS NULL",
                (slug,),
            )
            player = cur.fetchone()
            if not player:
                return None

            p_id = player["id"]
            # Singles win/loss logic
            cur.execute(
                """
                SELECT COUNT(*) as total, SUM(CASE WHEN winner_id = %s THEN 1 ELSE 0 END) as wins 
                FROM individual_matches 
                WHERE match_type = 'singles' AND (player_1_id = %s OR player_2_id = %s)
            """,
                (p_id, p_id, p_id),
            )
            singles = cur.fetchone()

            # Tournament count
            cur.execute(
                """
                SELECT COUNT(DISTINCT tournament_id) as count 
                FROM tournament_lineups 
                WHERE player_id = %s OR player_2_id = %s
            """,
                (p_id, p_id),
            )
            tourneys = cur.fetchone()

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


def get_tournament_history(conn, slug: str):
    """Fetches list of tournaments and points earned."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT t.name, t.start_date as date, t.logo_url, t.slug, tpp.total_points as points_earned,
                       tpp.final_placement as placement, tpp.category
                FROM tournament_player_points tpp
                JOIN tournaments t ON tpp.tournament_id = t.id
                JOIN players p ON tpp.player_id = p.id
                WHERE LOWER(p.slug) = LOWER(%s) ORDER BY t.start_date DESC
            """,
                (slug,),
            )
            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching history for {slug}: {e}", exc_info=True)
        raise


def get_player_match_history(conn, slug: str):
    """Fetches last 10 matches with stage and set details."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM players WHERE LOWER(slug) = LOWER(%s)", (slug,))
            player = cur.fetchone()
            if not player:
                return []

            p_id = player["id"]
            cur.execute(
                """
                SELECT 
                    im.id, im.category,
                    COALESCE(tg.group_name, im.match_type) as stage_name,
                    im.set_1_score, im.set_2_score, im.set_3_score,
                    im.winner_id,
                    p1.id as p1_id, CONCAT(p1.first_name, ' ', p1.last_name) as p1_name,
                    p2.id as p2_id, CONCAT(p2.first_name, ' ', p2.last_name) as p2_name,
                    %s as current_player_id
                FROM individual_matches im
                JOIN players p1 ON im.player_1_id = p1.id
                JOIN players p2 ON im.player_2_id = p2.id
                LEFT JOIN match_ties mt ON im.tie_id = mt.id
                LEFT JOIN tournament_groups tg ON mt.group_id = tg.id
                WHERE im.player_1_id = %s OR im.player_2_id = %s
                ORDER BY im.id DESC LIMIT 10
            """,
                (p_id, p_id, p_id),
            )
            return cur.fetchall()
    except Exception as e:
        logger.error(f"SQL Error in match history: {e}")
        return []
