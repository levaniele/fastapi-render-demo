from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Umpire(Base):
    __tablename__ = "umpires"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    image_url = Column(String(255), nullable=True)
    certification_level = Column(String(50), nullable=True)
    nationality_code = Column(String(10), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class Referee(Base):
    __tablename__ = "referees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    image_url = Column(String(255), nullable=True)
    certification_level = Column(String(50), nullable=True)
    nationality_code = Column(String(10), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
