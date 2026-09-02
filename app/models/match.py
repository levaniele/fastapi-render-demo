# ============================================================================
# FILE: app/models/match.py
# ORM Models for match-related tables
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class MatchTie(Base):
    __tablename__ = "match_ties"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, nullable=True) # Likely FK to tournament_groups
    
    tie_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)
    
    club_1_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    club_2_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    
    # Add other fields as discovered from usage
    
    matches = relationship("IndividualMatch", back_populates="tie")


class IndividualMatch(Base):
    __tablename__ = "individual_matches"

    id = Column(Integer, primary_key=True, index=True)
    tie_id = Column(Integer, ForeignKey("match_ties.id"), nullable=True)
    match_type = Column(String(50), nullable=True) # 'singles', 'doubles'
    category = Column(String(50), nullable=True)
    
    player_1_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    player_2_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    
    set_1_score = Column(String(20), nullable=True)
    set_2_score = Column(String(20), nullable=True)
    set_3_score = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)

    tie = relationship("MatchTie", back_populates="matches")
    rallies = relationship("MatchRally", back_populates="individual_match")
    
    # Relationships to players
    player_1 = relationship("Player", foreign_keys=[player_1_id])
    player_2 = relationship("Player", foreign_keys=[player_2_id])
    winner = relationship("Player", foreign_keys=[winner_id])


class MatchRally(Base):
    __tablename__ = "match_rallies"

    id = Column(Integer, primary_key=True, index=True)
    individual_match_id = Column(Integer, ForeignKey("individual_matches.id"), nullable=False)
    
    set_number = Column(Integer, nullable=False)
    server_side = Column(String(10), nullable=True) # 'team1', 'team2'
    rally_winner_side = Column(String(10), nullable=True) # 'team1', 'team2'
    
    # Additional rally details could go here

    individual_match = relationship("IndividualMatch", back_populates="rallies")
