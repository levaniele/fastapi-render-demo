# ============================================================================
# FILE: app/services/ranking_calculator.py
# Ranking Calculation Service - Calculates and updates player rankings
# ============================================================================

# ============================================================================
# SUMMARY OF SERVICE (RANKING_CALCULATOR):
# ============================================================================
# RankingCalculator.calculate_tournament_points(tournament_id) - Calculate & save tournament points
# Internal helpers: _calculate_placement_points, _calculate_match_points, _calculate_set_points, _save_tournament_points, _update_global_rankings, _update_rank_positions
# Used by: /rankings endpoints

from typing import Dict, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class RankingCalculator:
    """
    Service for calculating and updating player rankings based on tournament performance.

    Use `calculate_tournament_points(db: Session, tournament_id)` and pass a SQLAlchemy Session.
    """

    def __init__(self):
        pass

    def _get_point_value(
        self,
        db: Session,
        achievement_type: str,
        achievement_key: str,
        category: Optional[str] = None,
    ) -> int:
        """Get point value from configuration using SQLAlchemy session."""
        try:
            # Try category-specific first
            if category:
                res = db.execute(
                    text(
                        """
                        SELECT points
                        FROM ranking_point_config
                        WHERE achievement_type = :ach_type
                            AND achievement_key = :ach_key
                            AND category = :category
                            AND active = TRUE
                        """
                    ),
                    {"ach_type": achievement_type, "ach_key": achievement_key, "category": category},
                )

                result = res.mappings().first()
                if result:
                    return result["points"]

            # Fall back to general (NULL category)
            res = db.execute(
                text(
                    """
                    SELECT points
                    FROM ranking_point_config
                    WHERE achievement_type = :ach_type
                        AND achievement_key = :ach_key
                        AND category IS NULL
                        AND active = TRUE
                    """
                ),
                {"ach_type": achievement_type, "ach_key": achievement_key},
            )

            result = res.mappings().first()
            return result["points"] if result else 0

        except Exception as e:
            logger.error(f"Error getting point value: {e}")
            return 0

    def calculate_tournament_points(self, db: Session, tournament_id: int) -> Dict:
        """
        Calculate points for all players in a tournament using a SQLAlchemy session.
        Returns dict with player_id -> category -> points breakdown.
        """
        try:
            logger.info(f"Calculating points for tournament {tournament_id}")
            print(f"DEBUG: Starting calculation for tournament {tournament_id}")

            # Get tournament info
            res = db.execute(
                text(
                    """
                    SELECT
                        t.id,
                        t.name,
                        tw.first_place_player_id,
                        tw.second_place_player_id,
                        tw.third_place_player_id
                    FROM tournaments t
                    LEFT JOIN tournament_winners tw ON tw.tournament_id = t.id
                    WHERE t.id = :t_id AND t.deleted_at IS NULL
                    """
                ),
                {"t_id": tournament_id},
            )

            tournament = res.mappings().first()
            if not tournament:
                raise ValueError(f"Tournament {tournament_id} not found")

            player_points: dict[
                int, dict[str, dict]
            ] = {}  # {player_id: {category: {points breakdown}}}

            # Step 1: Calculate placement points
            self._calculate_placement_points(db, tournament_id, tournament, player_points)

            # Step 2: Calculate match win points
            self._calculate_match_points(db, tournament_id, player_points)

            # Step 3: Calculate set win points
            self._calculate_set_points(db, tournament_id, player_points)

            # Step 4: Save to database
            self._save_tournament_points(db, tournament_id, player_points)
            print(
                f"DEBUG: _save_tournament_points called with {len(player_points)} players"
            )
            print(f"DEBUG: player_points = {player_points}")

            # Step 5: Update global rankings
            self._update_global_rankings(db, player_points)

            # Step 6: Update rank positions
            self._update_rank_positions(db)

            logger.info(
                f"Successfully calculated points for {len(player_points)} players"
            )
            return player_points

        except Exception as e:
            logger.error(f"Error calculating tournament points: {e}")
            db.rollback()
            raise

    def _calculate_placement_points(
        self, db: Session, tournament_id: int, tournament: Dict, player_points: Dict
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
            res = db.execute(
                text(
                    """
                    SELECT DISTINCT tl.category
                    FROM tournament_lineups tl
                    WHERE tl.tournament_id = :t_id
                        AND (tl.player_id = :p OR tl.player_2_id = :p)
                    """
                ),
                {"t_id": tournament_id, "p": player_id},
            )

            categories = res.mappings().all()
            points = self._get_point_value(db, "placement", point_key)

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

    def _calculate_match_points(self, db: Session, tournament_id: int, player_points: Dict):
        """Calculate points for match wins."""
        print("DEBUG: Starting _calculate_match_points")

        # Get all matches in tournament
        res = db.execute(
            text(
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
                WHERE tg.tournament_id = :t_id
                    AND im.winner_id IS NOT NULL
                """
            ),
            {"t_id": tournament_id},
        )

        matches = res.mappings().all()

        for match in matches:
            category = match["category"]
            match_type = match["match_type"]
            winner_id = match["winner_id"]

            # Determine point key based on match type
            if match_type == "singles":
                point_key = "singles"
            else:  # doubles
                point_key = "doubles"

            points = self._get_point_value(db, "match_win", point_key, category)

            # For doubles, get all players on winning team
            if match_type == "doubles":
                r = db.execute(
                    text(
                        """
                        SELECT 
                            mdp.player_id,
                            mdp.team_side
                        FROM match_doubles_players mdp
                        WHERE mdp.match_id = :m_id
                        """
                    ),
                    {"m_id": match["match_id"]},
                )

                all_players = r.mappings().all()

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
                r2 = db.execute(
                    text(
                        """
                        SELECT player_id FROM match_doubles_players 
                        WHERE match_id = :m_id
                    """
                    ),
                    {"m_id": match["match_id"]},
                )
                all_participant_ids = [r["player_id"] for r in r2.mappings().all()]

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

    def _calculate_set_points(self, db: Session, tournament_id: int, player_points: Dict):
        """Calculate points for set wins."""
        print("DEBUG: Starting _calculate_set_points")

        # Get all matches with scores
        res = db.execute(
            text(
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
                WHERE tg.tournament_id = :t_id
                """
            ),
            {"t_id": tournament_id},
        )

        matches = res.mappings().all()

        for match in matches:
            category = match["category"]
            match_type = match["match_type"]

            # Get point value for set wins
            point_key = "singles" if match_type == "singles" else "doubles"
            points_per_set = self._get_point_value(db, "set_win", point_key)

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
                        r = db.execute(
                            text(
                                """
                                SELECT player_id 
                                FROM match_doubles_players 
                                WHERE match_id = :m_id AND team_side = :side
                            """
                            ),
                            {"m_id": match["match_id"], "side": set_winner_side},
                        )
                        winning_players = [rrow["player_id"] for rrow in r.mappings().all()]

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

    def _save_tournament_points(self, db: Session, tournament_id: int, player_points: Dict):
        """Save calculated points to tournament_player_points table."""
        print("DEBUG: Starting _save_tournament_points")

        for player_id, categories in player_points.items():
            for category, points_data in categories.items():
                total_points = (
                    points_data["placement_points"]
                    + points_data["match_win_points"]
                    + points_data["set_win_points"]
                )

                params = {
                    "tournament_id": tournament_id,
                    "player_id": player_id,
                    "category": category,
                    "placement_points": points_data["placement_points"],
                    "match_win_points": points_data["match_win_points"],
                    "set_win_points": points_data["set_win_points"],
                    "total_points": total_points,
                    "matches_played": points_data["matches_played"],
                    "matches_won": points_data["matches_won"],
                    "sets_won": points_data["sets_won"],
                    "sets_lost": points_data["sets_lost"],
                    "final_placement": points_data["final_placement"],
                }

                db.execute(
                    text(
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
                        ) VALUES (
                            :tournament_id, :player_id, :category, :placement_points,
                            :match_win_points, :set_win_points, :total_points, :matches_played,
                            :matches_won, :sets_won, :sets_lost, :final_placement
                        )
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
                        """
                    ),
                    params,
                )

        db.commit()
        logger.info(f"Saved tournament points for {len(player_points)} players")

    def _update_global_rankings(self, db: Session, player_points: Dict):
        """Update global player_rankings table with cumulative points."""
        print("DEBUG: Starting _update_global_rankings")
        for player_id, categories in player_points.items():
            for category, points_data in categories.items():
                print(f"DEBUG: Querying for player_id={player_id}, category={category}")

                # Get all tournament points for this player/category
                r = db.execute(
                    text(
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
                        WHERE player_id = :player_id AND category = :category
                        """
                    ),
                    {"player_id": player_id, "category": category},
                )

                totals = r.mappings().first()

                # Insert or update global ranking
                db.execute(
                    text(
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
                        ) VALUES (:player_id, :category, :total_points, :tournament_points, :match_points, :set_points, :tournaments_played, :matches_won, :matches_lost, :sets_won, :sets_lost, CURRENT_TIMESTAMP)
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
                        """
                    ),
                    {
                        "player_id": player_id,
                        "category": category,
                        "total_points": totals["total_points"],
                        "tournament_points": totals["tournament_points"],
                        "match_points": totals["match_points"],
                        "set_points": totals["set_points"],
                        "tournaments_played": totals["tournaments_played"],
                        "matches_won": totals["matches_won"],
                        "matches_lost": totals["matches_lost"],
                        "sets_won": totals["sets_won"],
                        "sets_lost": totals["sets_lost"],
                    },
                )

        db.commit()
        logger.info("Updated global rankings")

    def _update_rank_positions(self, db: Session):
        """Calculate and update rank positions for all players in each category."""

        categories = ["MS", "WS", "MD", "WD", "XD"]

        for category in categories:
            # Get all players in this category, ordered by points
            r = db.execute(
                text(
                    """
                    SELECT 
                        player_id,
                        total_points,
                        current_rank
                    FROM player_rankings
                    WHERE category = :category
                    ORDER BY total_points DESC, tournaments_played DESC, matches_won DESC
                    """
                ),
                {"category": category},
            )

            players = r.mappings().all()

            for rank, player in enumerate(players, start=1):
                previous_rank = player["current_rank"]

                # Update rank
                db.execute(
                    text(
                        """
                        UPDATE player_rankings
                        SET 
                            previous_rank = :previous_rank,
                            current_rank = :current_rank,
                            peak_rank = CASE 
                                WHEN peak_rank IS NULL OR :current_rank < peak_rank THEN :current_rank
                                ELSE peak_rank
                            END,
                            peak_rank_date = CASE
                                WHEN peak_rank IS NULL OR :current_rank < peak_rank THEN CURRENT_DATE
                                ELSE peak_rank_date
                            END
                        WHERE player_id = :player_id AND category = :category
                        """
                    ),
                    {
                        "previous_rank": previous_rank,
                        "current_rank": rank,
                        "player_id": player["player_id"],
                        "category": category,
                    },
                )

                # Record in history
                db.execute(
                    text(
                        """
                        INSERT INTO ranking_history (player_id, category, rank, total_points, recorded_at)
                        VALUES (:player_id, :category, :rank, :total_points, CURRENT_DATE)
                        ON CONFLICT (player_id, category, recorded_at)
                        DO UPDATE SET
                            rank = EXCLUDED.rank,
                            total_points = EXCLUDED.total_points
                        """
                    ),
                    {
                        "player_id": player["player_id"],
                        "category": category,
                        "rank": rank,
                        "total_points": player["total_points"],
                    },
                )

        db.commit()
        logger.info("Updated rank positions for all categories")


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


def calculate_rankings_for_tournament(tournament_id: int) -> Dict:
    """
    Convenience function to calculate rankings for a tournament.
    Can be called from API or scripts. Uses a SQLAlchemy Session.
    """
    db = SessionLocal()
    try:
        calculator = RankingCalculator()
        return calculator.calculate_tournament_points(db, tournament_id)
    finally:
        db.close()
