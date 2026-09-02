from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class CertificationLevel(Base):
    __tablename__ = "certification_levels"

    id = Column(Integer, primary_key=True, index=True)
    level_code = Column(String(20), unique=True, nullable=False)
    level_name = Column(String(50), nullable=False)
    level_type = Column(String(20), nullable=True)
    description = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )
