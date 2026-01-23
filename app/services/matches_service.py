"""
Services for Match operations
All database queries for matches-related endpoints
"""

# ============================================================================
# SUMMARY OF SERVICE (MATCHES):
# ============================================================================
# get_match_tie_by_id(db, tie_id)              - Fetch match tie and individual matches
# get_individual_match(db, match_id)           - Fetch single match details
# get_matches_by_category(db, category, limit) - List matches by category
# get_recent_matches(db, limit)               - Recent matches
# get_player_match_stats(db, player_id)       - Player match statistics
# get_head_to_head_stats(db, player1_id, player2_id) - Head-to-head stats
# Used by: /matches endpoints

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_match_tie_by_id(db: Session, tie_id: int):
    """
    Fetch complete match tie details including all individual matches.
    Returns: MatchTieResponse with individual_matches
    """
    try:
        # Get match tie details
        res = db.execute(
            text(
                """
                SELECT 
                    mt.id,
                    mt.group_id,
                    mt.club_1_id,
                    mt.club_2_id,
                    mt.overall_score,
                    mt.tie_date,
                    mt.tie_time,
                    c1.name as club_1_name,
                    c1.logo_url as club_1_logo,
                    c2.name as club_2_name,
                    c2.logo_url as club_2_logo,
                    tg.group_name as stage_label
                FROM match_ties mt
                JOIN tournament_groups tg ON mt.group_id = tg.id
                JOIN clubs c1 ON mt.club_1_id = c1.id
                JOIN clubs c2 ON mt.club_2_id = c2.id
                WHERE mt.id = :tie_id
                """
            ),
            {"tie_id": tie_id},
        )

        tie = res.mappings().first()

        if not tie:
            return None

        # Get individual matches
        r = db.execute(
            text(
                """
                SELECT 
                    im.id,
                    im.tie_id,
                    im.match_type,
                    im.category,
                    im.set_1_score,
                    im.set_2_score,
                    im.set_3_score,
                    im.duration_minutes,
                    im.winner_id,
                    im.player_1_id,
                    im.player_2_id,
                    CONCAT(p1.first_name, ' ', p1.last_name) as player_1_name,
                    CONCAT(p2.first_name, ' ', p2.last_name) as player_2_name,
                    CONCAT(w.first_name, ' ', w.last_name) as winner_name,
                    CONCAT(u.first_name, ' ', u.last_name) as umpire_name
                FROM individual_matches im
                LEFT JOIN players p1 ON im.player_1_id = p1.id
                LEFT JOIN players p2 ON im.player_2_id = p2.id
                LEFT JOIN players w ON im.winner_id = w.id
                LEFT JOIN umpires u ON im.umpire_id = u.id
                WHERE im.tie_id = :tie_id
                ORDER BY im.category
                """
            ),
            {"tie_id": tie_id},
        )

        matches = [dict(r) for r in r.mappings().all()]

        # For doubles matches, get all 4 players
        for match in matches:
            if match["match_type"] == "doubles":
                r2 = db.execute(
                    text(
                        """
                        SELECT 
                            mdp.player_id,
                            mdp.team_side,
                            CONCAT(p.first_name, ' ', p.last_name) as player_name
                        FROM match_doubles_players mdp
                        JOIN players p ON mdp.player_id = p.id
                        WHERE mdp.match_id = :m_id
                        ORDER BY mdp.team_side, mdp.player_id
                        """
                    ),
                    {"m_id": match["id"]},
                )

                doubles_players = [dict(rp) for rp in r2.mappings().all()]
                team_1 = [p for p in doubles_players if p["team_side"] == 1]
                team_2 = [p for p in doubles_players if p["team_side"] == 2]

                match["team_1_players"] = team_1
                match["team_2_players"] = team_2

        result = dict(tie)
        result["individual_matches"] = matches
        return result

    except Exception as e:
        logger.error(f"Error fetching match tie: {e}")
        raise


def get_individual_match(db: Session, match_id: int):
    """
    Fetch detailed information for a single individual match.
    Handles both singles and doubles matches.
    Returns: IndividualMatchResponse or DoublesMatchResponse
    """
    try:
        # Get match details
        r = db.execute(
            text(
                """
                SELECT 
                    im.id,
                    im.tie_id,
                    im.match_type,
                    im.category,
                    im.set_1_score,
                    im.set_2_score,
                    im.set_3_score,
                    im.duration_minutes,
                    im.winner_id,
                    im.player_1_id,
                    im.player_2_id,
                    im.umpire_id,
                    CONCAT(p1.first_name, ' ', p1.last_name) as player_1_name,
                    CONCAT(p2.first_name, ' ', p2.last_name) as player_2_name,
                    CONCAT(w.first_name, ' ', w.last_name) as winner_name,
                    CONCAT(u.first_name, ' ', u.last_name) as umpire_name,
                    im.created_at
                FROM individual_matches im
                LEFT JOIN players p1 ON im.player_1_id = p1.id
                LEFT JOIN players p2 ON im.player_2_id = p2.id
                LEFT JOIN players w ON im.winner_id = w.id
                LEFT JOIN umpires u ON im.umpire_id = u.id
                WHERE im.id = :match_id
                """
            ),
            {"match_id": match_id},
        )

        match = r.mappings().first()

        if not match:
            return None

        match = dict(match)

        # If doubles, get all players
        if match["match_type"] == "doubles":
            r2 = db.execute(
                text(
                    """
                    SELECT 
                        mdp.player_id,
                        mdp.team_side,
                        CONCAT(p.first_name, ' ', p.last_name) as player_name,
                        p.image_url
                    FROM match_doubles_players mdp
                    JOIN players p ON mdp.player_id = p.id
                    WHERE mdp.match_id = :match_id
                    ORDER BY mdp.team_side, mdp.player_id
                    """
                ),
                {"match_id": match_id},
            )

            doubles_players = [dict(rr) for rr in r2.mappings().all()]
            team_1 = [p for p in doubles_players if p["team_side"] == 1]
            team_2 = [p for p in doubles_players if p["team_side"] == 2]

            match["team_1_players"] = team_1
            match["team_2_players"] = team_2

        return match

    except Exception as e:
        logger.error(f"Error fetching individual match: {e}")
        raise

def get_matches_by_category(db: Session, category: str, limit: int = 50):
    """
    Fetch recent matches filtered by category.
    Category should be one of: MS, WS, MD, WD, XD
    Returns: List of matches
    """
    try:
        r = db.execute(
            text(
                """
                SELECT 
                    im.id,
                    im.match_type,
                    im.category,
                    im.set_1_score,
                    im.set_2_score,
                    im.set_3_score,
                    CONCAT(p1.first_name, ' ', p1.last_name) as player_1_name,
                    CONCAT(p2.first_name, ' ', p2.last_name) as player_2_name,
                    CONCAT(w.first_name, ' ', w.last_name) as winner_name,
                    t.name as tournament_name,
                    t.slug as tournament_slug,
                    mt.tie_date
                FROM individual_matches im
                JOIN match_ties mt ON im.tie_id = mt.id
                JOIN tournament_groups tg ON mt.group_id = tg.id
                JOIN tournaments t ON tg.tournament_id = t.id
                LEFT JOIN players p1 ON im.player_1_id = p1.id
                LEFT JOIN players p2 ON im.player_2_id = p2.id
                LEFT JOIN players w ON im.winner_id = w.id
                WHERE UPPER(im.category) = UPPER(:category)
                ORDER BY mt.tie_date DESC, im.id DESC
                LIMIT :limit
                """
            ),
            {"category": category, "limit": limit},
        )

        matches = [dict(r) for r in r.mappings().all()]

        # For doubles matches, add players info
        for match in matches:
            if match["match_type"] == "doubles":
                r2 = db.execute(
                    text(
                        """
                        SELECT 
                            mdp.team_side,
                            CONCAT(p.first_name, ' ', p.last_name) as player_name
                        FROM match_doubles_players mdp
                        JOIN players p ON mdp.player_id = p.id
                        WHERE mdp.match_id = :m_id
                        ORDER BY mdp.team_side
                        """
                    ),
                    {"m_id": match["id"]},
                )

                doubles_players = [dict(rr) for rr in r2.mappings().all()]
                match["doubles_players"] = doubles_players

        return matches if matches else []

    except Exception as e:
        logger.error(f"Error fetching matches by category: {e}")
        raise


def get_recent_matches(db: Session, limit: int = 20):
    """
    Fetch most recent matches across all tournaments.
    Returns: List of recent matches
    """
    try:
        r = db.execute(
            text(
                """
                SELECT 
                    im.id,
                    im.match_type,
                    im.category,
                    im.set_1_score,
                    im.set_2_score,
                    im.set_3_score,
                    CONCAT(p1.first_name, ' ', p1.last_name) as player_1_name,
                    CONCAT(p2.first_name, ' ', p2.last_name) as player_2_name,
                    CONCAT(w.first_name, ' ', w.last_name) as winner_name,
                    c1.name as club_1_name,
                    c2.name as club_2_name,
                    t.name as tournament_name,
                    t.slug as tournament_slug,
                    mt.tie_date
                FROM individual_matches im
                JOIN match_ties mt ON im.tie_id = mt.id
                JOIN clubs c1 ON mt.club_1_id = c1.id
                JOIN clubs c2 ON mt.club_2_id = c2.id
                JOIN tournament_groups tg ON mt.group_id = tg.id
                JOIN tournaments t ON tg.tournament_id = t.id
                LEFT JOIN players p1 ON im.player_1_id = p1.id
                LEFT JOIN players p2 ON im.player_2_id = p2.id
                LEFT JOIN players w ON im.winner_id = w.id
                WHERE t.deleted_at IS NULL
                ORDER BY mt.tie_date DESC, im.created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )

        matches = [dict(rr) for rr in r.mappings().all()]
        return matches if matches else []

    except Exception as e:
        logger.error(f"Error fetching recent matches: {e}")
        raise


def get_player_match_stats(db: Session, player_id: int):
    """
    Get match statistics for a specific player.
    Includes singles and doubles records.
    Returns: dict with statistics
    """
    try:
        # Check if player exists
        r = db.execute(
            text(
                """
                SELECT id, first_name, last_name 
                FROM players 
                WHERE id = :pid AND deleted_at IS NULL
                """
            ),
            {"pid": player_id},
        )

        player = r.mappings().first()

        if not player:
            return None

        # Singles statistics
        r2 = db.execute(
            text(
                """
                SELECT 
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN im.winner_id = :pid THEN 1 ELSE 0 END) as wins,
                    COUNT(*) - SUM(CASE WHEN im.winner_id = :pid THEN 1 ELSE 0 END) as losses
                FROM individual_matches im
                WHERE im.match_type = 'singles'
                    AND (im.player_1_id = :pid OR im.player_2_id = :pid)
                """
            ),
            {"pid": player_id},
        )

        singles = r2.mappings().first()

        # Doubles statistics
        r3 = db.execute(
            text(
                """
                SELECT 
                    COUNT(DISTINCT im.id) as total_matches,
                    SUM(CASE WHEN im.winner_id = :pid THEN 1 ELSE 0 END) as wins
                FROM individual_matches im
                JOIN match_doubles_players mdp ON im.id = mdp.match_id
                WHERE im.match_type = 'doubles'
                    AND mdp.player_id = :pid
                """
            ),
            {"pid": player_id},
        )

        doubles = r3.mappings().first()

        doubles_losses = (doubles["total_matches"] or 0) - (doubles["wins"] or 0)

        # Category breakdown
        r4 = db.execute(
            text(
                """
                SELECT 
                    im.category,
                    COUNT(*) as matches,
                    SUM(CASE WHEN im.winner_id = :pid THEN 1 ELSE 0 END) as wins
                FROM individual_matches im
                WHERE (im.player_1_id = :pid OR im.player_2_id = :pid)
                    OR (im.match_type = 'doubles' AND EXISTS (
                        SELECT 1 FROM match_doubles_players 
                        WHERE match_id = im.id AND player_id = :pid
                    ))
                GROUP BY im.category
                ORDER BY im.category
                """
            ),
            {"pid": player_id},
        )

        by_category = [dict(rr) for rr in r4.mappings().all()]

        return {
            "player_id": player_id,
            "player_name": f"{player['first_name']} {player['last_name']}",
            "singles": {
                "total": singles["total_matches"] or 0,
                "wins": singles["wins"] or 0,
                "losses": singles["losses"] or 0,
            },
            "doubles": {
                "total": doubles["total_matches"] or 0,
                "wins": doubles["wins"] or 0,
                "losses": doubles_losses,
            },
            "by_category": by_category if by_category else [],
        }

    except Exception as e:
        logger.error(f"Error fetching player match stats: {e}")
        raise

        by_category = cur.fetchall()

        return {
            "player_id": player_id,
            "player_name": f"{player['first_name']} {player['last_name']}",
            "singles": {
                "total": singles["total_matches"] or 0,
                "wins": singles["wins"] or 0,
                "losses": singles["losses"] or 0,
            },
            "doubles": {
                "total": doubles["total_matches"] or 0,
                "wins": doubles["wins"] or 0,
                "losses": doubles_losses,
            },
            "by_category": by_category if by_category else [],
        }

    except Exception as e:
        logger.error(f"Error fetching player match stats: {e}")
        raise
    finally:
        cur.close()


def get_head_to_head_stats(db: Session, player1_id: int, player2_id: int):
    """
    Get head-to-head statistics between two players.
    Returns: dict with head-to-head record
    """
    try:
        # Get all singles matches between these two players
        r = db.execute(
            text(
                """
                SELECT 
                    im.id,
                    im.category,
                    im.set_1_score,
                    im.set_2_score,
                    im.set_3_score,
                    im.winner_id,
                    t.name as tournament_name,
                    mt.tie_date
                FROM individual_matches im
                JOIN match_ties mt ON im.tie_id = mt.id
                JOIN tournament_groups tg ON mt.group_id = tg.id
                JOIN tournaments t ON tg.tournament_id = t.id
                WHERE im.match_type = 'singles'
                    AND ((im.player_1_id = :p1 AND im.player_2_id = :p2)
                         OR (im.player_1_id = :p2 AND im.player_2_id = :p1))
                ORDER BY mt.tie_date DESC
                """
            ),
            {"p1": player1_id, "p2": player2_id},
        )

        matches = [dict(rr) for rr in r.mappings().all()]

        player1_wins = sum(1 for m in matches if m["winner_id"] == player1_id)
        player2_wins = sum(1 for m in matches if m["winner_id"] == player2_id)

        return {
            "player1_id": player1_id,
            "player2_id": player2_id,
            "player1_wins": player1_wins,
            "player2_wins": player2_wins,
            "total_matches": len(matches),
            "matches": matches if matches else [],
        }

    except Exception as e:
        logger.error(f"Error fetching head-to-head stats: {e}")
        raise
