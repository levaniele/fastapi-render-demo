# ============================================================================
# FILE: app/models/tournament.py
# ORM MODELS: Database table model definitions
# ============================================================================

# ============================================================================
# SUMMARY OF MODELS:
# ============================================================================
# Tournament - ORM model for the 'tournaments' table
#   Key fields: id, name, slug, start_date, end_date, timezone,
#               organizer_organization_id, status, current_phase, last_completed_phase

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Boolean,
    SmallInteger,
    Computed,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Session
from app.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)

    # Required
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    # Phase 1 columns
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    timezone = Column(String(64), nullable=False, default="Europe/Tbilisi")

    organizer_organization_id = Column(Integer, nullable=False, index=True)

    status = Column(String(50), nullable=False, default="DRAFT")

    # Phase tracking columns
    current_phase = Column(
        SmallInteger, nullable=False, default=1
    )  # Where user should continue (1..7)
    last_completed_phase = Column(
        SmallInteger, nullable=False, default=0
    )  # Last fully completed phase (0..7)
    readiness_percent = Column(
        SmallInteger, Computed("ROUND(((current_phase - 1) * 100.0) / 6)::int")
    )  # Generated column (0..100)

    # Optional registration
    registration_deadline_at = Column(DateTime, nullable=True)

    # Optional branding
    logo_url = Column(String(255), nullable=True)
    banner_url = Column(String(255), nullable=True)

    # Optional invitations
    invites_enabled = Column(Boolean, nullable=False, default=False)
    invites_open_at = Column(DateTime, nullable=True)
    invites_close_at = Column(DateTime, nullable=True)

    # Registration settings
    public_registration = Column(Boolean, nullable=False, default=True)
    allow_waitlist = Column(Boolean, nullable=False, default=False)
    show_bracket_publicly = Column(Boolean, nullable=False, default=False)
    auto_approve_entries = Column(Boolean, nullable=False, default=False)
    allow_entry_editing = Column(Boolean, nullable=False, default=True)

    # Venue/scheduling settings
    venue_mode = Column(String(10), nullable=False, default="single")
    avg_match_duration_min = Column(Integer, nullable=True)
    match_buffer_min = Column(Integer, nullable=True)
    enforce_quiet_hours = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    venue = relationship("TournamentVenue", uselist=False, back_populates="tournament")
    events = relationship("TournamentEvent", back_populates="tournament")
    courts = relationship("TournamentCourt", back_populates="tournament")
    time_blocks = relationship("TournamentTimeBlock", back_populates="tournament")
    entries = relationship("TournamentEntry", back_populates="tournament")
    winners = relationship("TournamentWinner", uselist=False, back_populates="tournament")


class TournamentVenue(Base):
    __tablename__ = "tournament_venues"

    # id = Column(Integer, primary_key=True, index=True) # Table has no ID column
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), primary_key=True, nullable=False, unique=True)
    venue_name = Column(String(255), nullable=True)
    venue_city = Column(String(100), nullable=True)
    venue_country_code = Column(String(10), nullable=True)
    location = Column(String(255), nullable=True)

    tournament = relationship("Tournament", back_populates="venue")


class TournamentEvent(Base):
    __tablename__ = "tournament_events"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    event_name = Column(String(100), nullable=True)
    discipline = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    level = Column(String(50), nullable=True)
    scoring_format = Column(String(50), nullable=True)
    max_entries = Column(Integer, nullable=True)
    entry_fee = Column(Integer, nullable=True)
    currency = Column(String(10), nullable=True)
    member_perks = Column(String(255), nullable=True) # Check type, inferred string
    draw_type = Column(String(50), nullable=True)
    draw_setup = Column(JSONB, nullable=True)
    generation_rules = Column(JSONB, nullable=True)
    seeding_mode = Column(String(50), nullable=True)
    lock_entries = Column(Boolean, default=False)
    publish_bracket_preview = Column(Boolean, default=False)
    bracket_visibility = Column(String(50), nullable=True)

    tournament = relationship("Tournament", back_populates="events")


class TournamentCourt(Base):
    __tablename__ = "tournament_courts"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    court_name = Column(String(100), nullable=False)
    court_number = Column(Integer, nullable=True)
    venue_label = Column(String(100), nullable=True)

    tournament = relationship("Tournament", back_populates="courts")


class TournamentTimeBlock(Base):
    __tablename__ = "tournament_time_blocks"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    block_type = Column(String(50), nullable=True)
    block_label = Column(String(100), nullable=True)
    block_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False) # Stored as string in SQL?
    end_time = Column(String(10), nullable=False)
    lunch_break_enabled = Column(Boolean, default=False)
    break_start_time = Column(String(10), nullable=True)
    break_end_time = Column(String(10), nullable=True)

    tournament = relationship("Tournament", back_populates="time_blocks")


class TournamentEntry(Base):
    __tablename__ = "tournament_entries"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    event_id = Column(Integer, nullable=True) # Should likely be FK to events
    entry_name = Column(String(255), nullable=False)
    entry_type = Column(String(50), nullable=True)
    entry_category = Column(String(50), nullable=True)
    entry_discipline = Column(String(50), nullable=True)
    approval_status = Column(String(50), nullable=True)

    tournament = relationship("Tournament", back_populates="entries")


class TournamentWinner(Base):
    __tablename__ = "tournament_winners"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False, unique=True)
    
    first_place_club_id = Column(Integer, nullable=True)
    second_place_club_id = Column(Integer, nullable=True)
    third_place_club_id = Column(Integer, nullable=True)
    
    first_place_player_id = Column(Integer, nullable=True)
    second_place_player_id = Column(Integer, nullable=True)
    third_place_player_id = Column(Integer, nullable=True)

    tournament = relationship("Tournament", back_populates="winners")


class TournamentGroup(Base):
    __tablename__ = "tournament_groups"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    group_name = Column(String(100), nullable=False)
    
    # Add other fields as discovered logic
    
    # Relationship
    # tournament = relationship("Tournament") # Optional backref

class TournamentGroupMember(Base):
    __tablename__ = "tournament_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("tournament_groups.id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    # Add ranking/points if needed later

class TournamentLineup(Base):
    __tablename__ = "tournament_lineups"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    player_2_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    category = Column(String(20), nullable=True)

class TournamentCoach(Base):
    __tablename__ = "tournament_coaches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    assigned_role = Column(String(50), nullable=True)

class TournamentUmpire(Base):
    __tablename__ = "tournament_umpires"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    umpire_id = Column(Integer, ForeignKey("umpires.id"), nullable=False)
    assigned_role = Column(String(50), nullable=True)
