from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Boolean,
    SmallInteger,
    Computed,
)
from sqlalchemy.sql import func
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
