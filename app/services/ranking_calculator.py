# ============================================================================
# FILE: app/services/ranking_calculator.py
# Ranking Calculation Service - Calculates and updates player rankings
# ============================================================================

from typing import Dict, Optional
import logging
from psycopg2.extras import RealDictCursor
from app.database import get_db

logger = logging.getLogger(__name__)


class RankingCalculator:
    """
    Service for calculating and updating player rankings based on tournament performance.
    """

    def __init__(self):
        self.conn = None
        self.cur = None

    def _get_point_value(
        self,
        achievement_type: str,
        achievement_key: str,
        category: Optional[str] = None,
    ) -> int:
        """Get point value from configuration."""
        try:
            # Try category-specific first
            if category:
                self.cur.execute(
                    """
                    SELECT points 
                    FROM ranking_point_config 
                    WHERE achievement_type = %s 
                        AND achievement_key = %s 
                        AND category = %s
                        AND active = TRUE
                """,
                    (achievement_type, achievement_key, category),
                )

                result = self.cur.fetchone()
                if result:
                    return result["points"]

            # Fall back to general (NULL category)
            self.cur.execute(
                """
                SELECT points 
                FROM ranking_point_config 
                WHERE achievement_type = %s 
                    AND achievement_key = %s 
                    AND category IS NULL
                    AND active = TRUE
            """,
                (achievement_type, achievement_key),
            )

            result = self.cur.fetchone()
            return result["points"] if result else 0

        except Exception as e:
            logger.error(f"Error getting point value: {e}")
            return 0

    def calculate_tournament_points(self, tournament_id: int) -> Dict:
        """
        Calculate points for all players in a tournament.
        Returns dict with player_id -> category -> points breakdown.
        """
        self.conn = get_db()
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

        try:
            logger.info(f"Calculating points for tournament {tournament_id}")
            print(f"DEBUG: Starting calculation for tournament {tournament_id}")

            # Get tournament info
            self.cur.execute(
                """
                SELECT
                    t.id,
                    t.name,
                    tw.first_place_player_id,
                    tw.second_place_player_id,
                    tw.third_place_player_id
                FROM tournaments t
                LEFT JOIN tournament_winners tw ON tw.tournament_id = t.id
                WHERE t.id = %s AND t.deleted_at IS NULL
            """,
                (tournament_id,),
            )

            tournament = self.cur.fetchone()
            if not tournament:
                raise ValueError(f"Tournament {tournament_id} not found")

            player_points: dict[
                int, dict[str, dict]
            ] = {}  # {player_id: {category: {points breakdown}}}

            # Step 1: Calculate placement points
            self._calculate_placement_points(tournament_id, tournament, player_points)

            # Step 2: Calculate match win points
            self._calculate_match_points(tournament_id, player_points)

            # Step 3: Calculate set win points
            self._calculate_set_points(tournament_id, player_points)

            # Step 4: Save to database
            self._save_tournament_points(tournament_id, player_points)
            print(
                f"DEBUG: _save_tournament_points called with {len(player_points)} players"
            )
            print(f"DEBUG: player_points = {player_points}")

            # Step 5: Update global rankings
            self._update_global_rankings(player_points)

            # Step 6: Update rank positions
            self._update_rank_positions()

            logger.info(
                f"Successfully calculated points for {len(player_points)} players"
            )
            return player_points

        except Exception as e:
            logger.error(f"Error calculating tournament points: {e}")
            self.conn.rollback()
            raise
        finally:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()

    def _calculate_placement_points(
        self, tournament_id: int, tournament: Dict, player_points: Dict
    ):
        """Calculate points based on final tournament placement."""
        print("DEBUG: Starting _calculate_placement_points")
        # Map placement fields to point keys
        placement_map = {
            "first_place_player_id": "1st_place",
            "second_place_player_id": "2nd_place",
            "third_place_player_id": "3rd_place",
        }

        for db_field, point_key in placement_map.items():
            player_id = tournament.get(db_field)
            if not player_id:
                continue

            # Get tournament categories for the placed player
            self.cur.execute(
                """
                SELECT DISTINCT tl.category
                FROM tournament_lineups tl
                WHERE tl.tournament_id = %s
                    AND (tl.player_id = %s OR tl.player_2_id = %s)
            """,
                (tournament_id, player_id, player_id),
            )

            categories = self.cur.fetchall()
            points = self._get_point_value("placement", point_key)

            for row in categories:
                category = row["category"]

                if player_id not in player_points:
                    player_points[player_id] = {}
                if category not in player_points[player_id]:
                    player_points[player_id][category] = {
                        "placement_points": 0,
                        "match_win_points": 0,
                        "set_win_points": 0,
                        "matches_played": 0,
                        "matches_won": 0,
                        "sets_won": 0,
                        "sets_lost": 0,
                        "final_placement": None,
                    }

                player_points[player_id][category]["placement_points"] = points
                player_points[player_id][category]["final_placement"] = (
                    point_key.replace("_", " ").title()
                )

                logger.debug(
                    f"Player {player_id} ({category}): {points} placement points ({point_key})"
                )

    def _calculate_match_points(self, tournament_id: int, player_points: Dict):
        """Calculate points for match wins."""
        print("DEBUG: Starting _calculate_match_points")

        # Get all matches in tournament
        self.cur.execute(
            """
            SELECT 
                im.id as match_id,
                im.category,
                im.match_type,
                im.player_1_id,
                im.player_2_id,
                im.winner_id,
                im.set_1_score,
                im.set_2_score,
                im.set_3_score
            FROM individual_matches im
            JOIN match_ties mt ON im.tie_id = mt.id
            JOIN tournament_groups tg ON mt.group_id = tg.id
            WHERE tg.tournament_id = %s
                AND im.winner_id IS NOT NULL
        """,
            (tournament_id,),
        )

        matches = self.cur.fetchall()

        for match in matches:
            category = match["category"]
            match_type = match["match_type"]
            winner_id = match["winner_id"]

            # Determine point key based on match type
            if match_type == "singles":
                point_key = "singles"
            else:  # doubles
                point_key = "doubles"

            points = self._get_point_value("match_win", point_key, category)

            # For doubles, get all players on winning team
            if match_type == "doubles":
                self.cur.execute(
                    """
                    SELECT 
                        mdp.player_id,
                        mdp.team_side
                    FROM match_doubles_players mdp
                    WHERE mdp.match_id = %s
                """,
                    (match["match_id"],),
                )

                all_players = self.cur.fetchall()

                # Find winner's team side
                winner_team = None
                for p in all_players:
                    if p["player_id"] == winner_id:
                        winner_team = p["team_side"]
                        break

                # Award points to all players on winning team
                winning_players = [
                    p["player_id"] for p in all_players if p["team_side"] == winner_team
                ]
            else:
                # Singles - just the winner
                winning_players = [winner_id]

            # Award points
            for player_id in winning_players:
                if player_id not in player_points:
                    player_points[player_id] = {}
                if category not in player_points[player_id]:
                    player_points[player_id][category] = {
                        "placement_points": 0,
                        "match_win_points": 0,
                        "set_win_points": 0,
                        "matches_played": 0,
                        "matches_won": 0,
                        "sets_won": 0,
                        "sets_lost": 0,
                        "final_placement": None,
                    }

                player_points[player_id][category]["match_win_points"] += points
                player_points[player_id][category]["matches_won"] += 1

            # Track matches played for all participants
            all_participant_ids = []
            if match_type == "singles":
                all_participant_ids = [match["player_1_id"], match["player_2_id"]]
            else:
                self.cur.execute(
                    """
                    SELECT player_id FROM match_doubles_players 
                    WHERE match_id = %s
                """,
                    (match["match_id"],),
                )
                all_participant_ids = [r["player_id"] for r in self.cur.fetchall()]

            for player_id in all_participant_ids:
                if player_id not in player_points:
                    player_points[player_id] = {}
                if category not in player_points[player_id]:
                    player_points[player_id][category] = {
                        "placement_points": 0,
                        "match_win_points": 0,
                        "set_win_points": 0,
                        "matches_played": 0,
                        "matches_won": 0,
                        "sets_won": 0,
                        "sets_lost": 0,
                        "final_placement": None,
                    }

                player_points[player_id][category]["matches_played"] += 1

    def _calculate_set_points(self, tournament_id: int, player_points: Dict):
        """Calculate points for set wins."""
        print("DEBUG: Starting _calculate_set_points")

        # Get all matches with scores
        self.cur.execute(
            """
            SELECT 
                im.id as match_id,
                im.category,
                im.match_type,
                im.player_1_id,
                im.player_2_id,
                im.set_1_score,
                im.set_2_score,
                im.set_3_score,
                im.duration_minutes
            FROM individual_matches im
            JOIN match_ties mt ON im.tie_id = mt.id
            JOIN tournament_groups tg ON mt.group_id = tg.id
            WHERE tg.tournament_id = %s
        """,
            (tournament_id,),
        )

        matches = self.cur.fetchall()

        for match in matches:
            category = match["category"]
            match_type = match["match_type"]

            # Get point value for set wins
            point_key = "singles" if match_type == "singles" else "doubles"
            points_per_set = self._get_point_value("set_win", point_key)

            # Parse set scores
            sets = [match["set_1_score"], match["set_2_score"], match["set_3_score"]]

            for set_score in sets:
                if not set_score or set_score == "[default]":
                    continue

                try:
                    parts = set_score.split("-")
                    score1 = int(parts[0])
                    score2 = int(parts[1])

                    # Determine set winner (higher score)
                    if score1 > score2:
                        set_winner_side = 1
                    elif score2 > score1:
                        set_winner_side = 2
                    else:
                        continue  # Tie? Skip

                    # Get players on winning side
                    if match_type == "singles":
                        winning_player = (
                            match["player_1_id"]
                            if set_winner_side == 1
                            else match["player_2_id"]
                        )
                        winning_players = [winning_player]
                    else:
                        # Doubles - get team
                        self.cur.execute(
                            """
                            SELECT player_id 
                            FROM match_doubles_players 
                            WHERE match_id = %s AND team_side = %s
                        """,
                            (match["match_id"], set_winner_side),
                        )
                        winning_players = [r["player_id"] for r in self.cur.fetchall()]

                    # Award set points
                    for player_id in winning_players:
                        if player_id not in player_points:
                            player_points[player_id] = {}
                        if category not in player_points[player_id]:
                            player_points[player_id][category] = {
                                "placement_points": 0,
                                "match_win_points": 0,
                                "set_win_points": 0,
                                "matches_played": 0,
                                "matches_won": 0,
                                "sets_won": 0,
                                "sets_lost": 0,
                                "final_placement": None,
                            }

                        player_points[player_id][category]["set_win_points"] += (
                            points_per_set
                        )
                        player_points[player_id][category]["sets_won"] += 1

                except (ValueError, IndexError):
                    logger.warning(f"Could not parse set score: {set_score}")
                    continue

    def _save_tournament_points(self, tournament_id: int, player_points: Dict):
        """Save calculated points to tournament_player_points table."""
        print("DEBUG: Starting _save_tournament_points")

        for player_id, categories in player_points.items():
            for category, points_data in categories.items():
                total_points = (
                    points_data["placement_points"]
                    + points_data["match_win_points"]
                    + points_data["set_win_points"]
                )

                # Insert or update
                self.cur.execute(
                    """
                    INSERT INTO tournament_player_points (
                        tournament_id,
                        player_id,
                        category,
                        placement_points,
                        match_win_points,
                        set_win_points,
                        total_points,
                        matches_played,
                        matches_won,
                        sets_won,
                        sets_lost,
                        final_placement
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tournament_id, player_id, category)
                    DO UPDATE SET
                        placement_points = EXCLUDED.placement_points,
                        match_win_points = EXCLUDED.match_win_points,
                        set_win_points = EXCLUDED.set_win_points,
                        total_points = EXCLUDED.total_points,
                        matches_played = EXCLUDED.matches_played,
                        matches_won = EXCLUDED.matches_won,
                        sets_won = EXCLUDED.sets_won,
                        sets_lost = EXCLUDED.sets_lost,
                        final_placement = EXCLUDED.final_placement,
                        awarded_at = CURRENT_TIMESTAMP
                """,
                    (
                        tournament_id,
                        player_id,
                        category,
                        points_data["placement_points"],
                        points_data["match_win_points"],
                        points_data["set_win_points"],
                        total_points,
                        points_data["matches_played"],
                        points_data["matches_won"],
                        points_data["sets_won"],
                        points_data["sets_lost"],
                        points_data["final_placement"],
                    ),
                )

        self.conn.commit()
        logger.info(f"Saved tournament points for {len(player_points)} players")

    def _update_global_rankings(self, player_points: Dict):
        """Update global player_rankings table with cumulative points."""
        print("DEBUG: Starting _update_global_rankings")
        for player_id, categories in player_points.items():
            for category, points_data in categories.items():
                print(f"DEBUG: Querying for player_id={player_id}, category={category}")

                # Get all tournament points for this player/category
                self.cur.execute(
                    """
                    SELECT 
                        COALESCE(SUM(total_points), 0) as total_points,
                        COALESCE(SUM(placement_points), 0) as tournament_points,
                        COALESCE(SUM(match_win_points), 0) as match_points,
                        COALESCE(SUM(set_win_points), 0) as set_points,
                        COUNT(DISTINCT tournament_id) as tournaments_played,
                        COALESCE(SUM(matches_won), 0) as matches_won,
                        COALESCE(SUM(matches_played) - SUM(matches_won), 0) as matches_lost,
                        COALESCE(SUM(sets_won), 0) as sets_won,
                        COALESCE(SUM(sets_lost), 0) as sets_lost
                    FROM tournament_player_points
                    WHERE player_id = %s AND category = %s
                """,
                    (player_id, category),
                )

                totals = self.cur.fetchone()

                # Insert or update global ranking
                self.cur.execute(
                    """
                    INSERT INTO player_rankings (
                        player_id,
                        category,
                        total_points,
                        tournament_points,
                        match_points,
                        set_points,
                        tournaments_played,
                        matches_won,
                        matches_lost,
                        sets_won,
                        sets_lost,
                        last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (player_id, category)
                    DO UPDATE SET
                        total_points = EXCLUDED.total_points,
                        tournament_points = EXCLUDED.tournament_points,
                        match_points = EXCLUDED.match_points,
                        set_points = EXCLUDED.set_points,
                        tournaments_played = EXCLUDED.tournaments_played,
                        matches_won = EXCLUDED.matches_won,
                        matches_lost = EXCLUDED.matches_lost,
                        sets_won = EXCLUDED.sets_won,
                        sets_lost = EXCLUDED.sets_lost,
                        last_updated = CURRENT_TIMESTAMP
                """,
                    (
                        player_id,
                        category,
                        totals["total_points"],
                        totals["tournament_points"],
                        totals["match_points"],
                        totals["set_points"],
                        totals["tournaments_played"],
                        totals["matches_won"],
                        totals["matches_lost"],
                        totals["sets_won"],
                        totals["sets_lost"],
                    ),
                )

        self.conn.commit()
        logger.info("Updated global rankings")

    def _update_rank_positions(self):
        """Calculate and update rank positions for all players in each category."""

        categories = ["MS", "WS", "MD", "WD", "XD"]

        for category in categories:
            # Get all players in this category, ordered by points
            self.cur.execute(
                """
                SELECT 
                    player_id,
                    total_points,
                    current_rank
                FROM player_rankings
                WHERE category = %s
                ORDER BY total_points DESC, tournaments_played DESC, matches_won DESC
            """,
                (category,),
            )

            players = self.cur.fetchall()

            for rank, player in enumerate(players, start=1):
                previous_rank = player["current_rank"]

                # Update rank
                self.cur.execute(
                    """
                    UPDATE player_rankings
                    SET 
                        previous_rank = %s,
                        current_rank = %s,
                        peak_rank = CASE 
                            WHEN peak_rank IS NULL OR %s < peak_rank THEN %s
                            ELSE peak_rank
                        END,
                        peak_rank_date = CASE
                            WHEN peak_rank IS NULL OR %s < peak_rank THEN CURRENT_DATE
                            ELSE peak_rank_date
                        END
                    WHERE player_id = %s AND category = %s
                """,
                    (
                        previous_rank,
                        rank,
                        rank,
                        rank,
                        rank,
                        player["player_id"],
                        category,
                    ),
                )

                # Record in history
                self.cur.execute(
                    """
                    INSERT INTO ranking_history (player_id, category, rank, total_points, recorded_at)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE)
                    ON CONFLICT (player_id, category, recorded_at)
                    DO UPDATE SET
                        rank = EXCLUDED.rank,
                        total_points = EXCLUDED.total_points
                """,
                    (player["player_id"], category, rank, player["total_points"]),
                )

        self.conn.commit()
        logger.info("Updated rank positions for all categories")


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


def calculate_rankings_for_tournament(tournament_id: int) -> Dict:
    """
    Convenience function to calculate rankings for a tournament.
    Can be called from API or scripts.
    """
    calculator = RankingCalculator()
    return calculator.calculate_tournament_points(tournament_id)
