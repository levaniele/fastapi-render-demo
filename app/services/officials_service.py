"""
Services for Officials operations
All database queries for umpires and referees endpoints
"""

# ============================================================================
# SUMMARY OF SERVICE (OFFICIALS):
# ============================================================================
# get_all_umpires(db)               - List umpires
# get_umpire_by_slug(db, slug)      - Get umpire details
# get_umpire_stats_by_slug(db, slug)- Get umpire match history and stats
# get_all_referees(db)              - List referees
# get_referee_by_slug(db, slug)     - Get referee details
# Used by: /officials endpoints

import logging
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_all_umpires(db):
    """
    Fetch all active umpires from the database.
    Returns: List[UmpireResponse]
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT 
                id,
                first_name, 
                last_name, 
                slug, 
                image_url, 
                certification_level,
                nationality_code
            FROM umpires
            WHERE deleted_at IS NULL
            ORDER BY last_name, first_name
        """)

        umpires = cur.fetchall()
        return umpires if umpires else []

    except Exception as e:
        logger.error(f"Error fetching umpires: {e}")
        raise
    finally:
        cur.close()


def get_umpire_by_slug(db, slug: str):
    """
    Fetch a single umpire profile by their unique slug.
    Returns: UmpireResponse
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT * FROM umpires 
            WHERE slug = %s AND deleted_at IS NULL
        """,
            (slug,),
        )

        umpire = cur.fetchone()
        return umpire

    except Exception as e:
        logger.error(f"Error fetching umpire details: {e}")
        raise
    finally:
        cur.close()


# ============================================================================
# FILE: app/services/officials_service.py
# ============================================================================


def get_umpire_stats_by_slug(db, slug: str):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Fetch Umpire Basic Details
        cur.execute(
            """
            SELECT 
                id, first_name, last_name, slug, 
                image_url, certification_level, nationality_code
            FROM umpires 
            WHERE slug = %s AND deleted_at IS NULL
        """,
            (slug,),
        )
        umpire = cur.fetchone()

        if not umpire:
            return None

        # 2. Fetch Matches (Handling Singles AND Doubles)
        # We use CASE statements and Subqueries to format names correctly based on match_type.
        cur.execute(
            """
            SELECT 
                m.id, 
                m.tie_id, 
                m.match_type, 
                m.category, 
                m.set_1_score, 
                m.set_2_score, 
                m.set_3_score, 
                m.duration_minutes,
                
                -- PLAYER 1 NAME (Singles vs Doubles)
                CASE 
                    WHEN m.match_type = 'singles' THEN CONCAT(p1.first_name, ' ', p1.last_name)
                    ELSE (
                        SELECT STRING_AGG(p.last_name, ' / ')
                        FROM match_doubles_players mdp
                        JOIN players p ON mdp.player_id = p.id
                        WHERE mdp.match_id = m.id AND mdp.team_side = 1
                    )
                END as player_1_name,

                -- PLAYER 2 NAME (Singles vs Doubles)
                CASE 
                    WHEN m.match_type = 'singles' THEN CONCAT(p2.first_name, ' ', p2.last_name)
                    ELSE (
                        SELECT STRING_AGG(p.last_name, ' / ')
                        FROM match_doubles_players mdp
                        JOIN players p ON mdp.player_id = p.id
                        WHERE mdp.match_id = m.id AND mdp.team_side = 2
                    )
                END as player_2_name,

                -- WINNER NAME (Singles vs Doubles)
                CASE 
                    WHEN m.winner_id IS NULL THEN NULL
                    WHEN m.match_type = 'singles' THEN CONCAT(pw.first_name, ' ', pw.last_name)
                    ELSE (
                        -- For doubles, find the side that the winner_id belongs to, and show that pair
                        SELECT STRING_AGG(p.last_name, ' / ')
                        FROM match_doubles_players mdp_win
                        JOIN players p ON mdp_win.player_id = p.id
                        WHERE mdp_win.match_id = m.id 
                          AND mdp_win.team_side = (
                              SELECT team_side FROM match_doubles_players 
                              WHERE match_id = m.id AND player_id = m.winner_id LIMIT 1
                          )
                    )
                END as winner_name,

                -- Tournament Info
                t.id as tournament_id,
                t.name as tournament_name,
                t.slug as tournament_slug,
                t.start_date as tournament_date,
                t.logo_url as tournament_logo

            FROM individual_matches m
            JOIN match_ties tie ON m.tie_id = tie.id
            JOIN tournament_groups tg ON tie.group_id = tg.id 
            JOIN tournaments t ON tg.tournament_id = t.id
            
            -- Joins for Singles Players (Still useful for Singles matches)
            LEFT JOIN players p1 ON m.player_1_id = p1.id
            LEFT JOIN players p2 ON m.player_2_id = p2.id
            LEFT JOIN players pw ON m.winner_id = pw.id
            
            WHERE m.umpire_id = %s
            ORDER BY t.start_date DESC, m.id DESC
        """,
            (umpire["id"],),
        )

        raw_matches = cur.fetchall()

        # 3. Process Data
        matches_list = []
        seen_tournaments = set()
        tournaments_list = []

        for row in raw_matches:
            matches_list.append(
                {
                    "id": row["id"],
                    "tie_id": row["tie_id"],
                    "match_type": row["match_type"],
                    "category": row["category"],
                    "set_1_score": row["set_1_score"],
                    "set_2_score": row["set_2_score"],
                    "set_3_score": row["set_3_score"],
                    "duration_minutes": row["duration_minutes"],
                    # These will now contain data for both Singles and Doubles
                    "player_1_name": row["player_1_name"],
                    "player_2_name": row["player_2_name"],
                    "winner_name": row["winner_name"],
                    # Context
                    "umpire_name": f"{umpire['first_name']} {umpire['last_name']}",
                    "tournament_name": row["tournament_name"],
                    "tournament_date": row["tournament_date"],
                }
            )

            t_id = row["tournament_id"]
            if t_id not in seen_tournaments:
                seen_tournaments.add(t_id)
                tournaments_list.append(
                    {
                        "id": row["tournament_id"],
                        "name": row["tournament_name"],
                        "slug": row["tournament_slug"],
                        "start_date": row["tournament_date"],
                        "logo_url": row["tournament_logo"],
                    }
                )

        return {
            **umpire,
            "total_matches": len(matches_list),
            "total_tournaments": len(tournaments_list),
            "matches": matches_list,
            "tournaments": tournaments_list,
        }

    finally:
        cur.close()


def get_all_referees(db):
    """
    Fetch all active referees from the database.
    Returns: List[RefereeResponse]
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT 
                id, 
                first_name, 
                last_name, 
                slug, 
                image_url, 
                certification_level, 
                nationality_code
            FROM referees 
            WHERE deleted_at IS NULL
            ORDER BY last_name
        """)

        referees = cur.fetchall()
        return referees if referees else []

    except Exception as e:
        logger.error(f"Error fetching referees: {e}")
        raise
    finally:
        cur.close()


def get_referee_by_slug(db, slug: str):
    """
    Fetch a single referee profile by their unique slug.
    Returns: RefereeResponse
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            SELECT * FROM referees 
            WHERE slug = %s AND deleted_at IS NULL
        """,
            (slug,),
        )

        referee = cur.fetchone()
        return referee

    except Exception as e:
        logger.error(f"Error fetching referee details: {e}")
        raise
    finally:
        cur.close()
