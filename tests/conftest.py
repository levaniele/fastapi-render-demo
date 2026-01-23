import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.main
from app.database import Base, get_db_session
# Ensure all models are imported so Base.metadata knows them
import app.models 

# Use the test database URL (copied from .env but pointing to badminton_test)
TEST_DATABASE_URL = "postgresql://badminton_user:Badaxosi8@localhost:5432/badminton_test?sslmode=disable"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_app():
    return app.main.app

@pytest.fixture(scope="module")
def test_db():
    # Clean output state first
    Base.metadata.drop_all(bind=engine)
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Manually create player_rankings table (missing from models/alembic)
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS player_rankings CASCADE")) # Force cleanup
        conn.execute(text("""
            CREATE TABLE player_rankings (
                player_id INTEGER,
                category VARCHAR(20),
                current_rank INTEGER,
                previous_rank INTEGER,
                total_points INTEGER DEFAULT 0,
                tournament_points INTEGER DEFAULT 0,
                match_points INTEGER DEFAULT 0,
                set_points INTEGER DEFAULT 0,
                tournaments_played INTEGER DEFAULT 0,
                matches_won INTEGER DEFAULT 0,
                matches_lost INTEGER DEFAULT 0,
                sets_won INTEGER DEFAULT 0,
                sets_lost INTEGER DEFAULT 0,
                peak_rank INTEGER,
                peak_rank_date TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (player_id, category)
            );
        """))
        conn.commit()
    
    yield
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    # Override the dependency to use our test DB session
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.main.app.dependency_overrides[get_db_session] = override_get_db
    # Using TestClient as context manager might close app? No.
    # But clean client each time is safer.
    with TestClient(app.main.app) as c:
        yield c
        c.cookies.clear() # Verify cookies cleared

@pytest.fixture(scope="function", autouse=True)
def seed_db():
    # Insert default organization for tests
    db = TestingSessionLocal()
    try:
        from app.models.organization import Organization
        org = Organization(id=1, slug="default-org", name="Default Org", short_name="DO")
        db.add(org)
        db.commit()
    except Exception:
        db.rollback()
        # Ignore if exists (though tables dropped each time so it shouldn't)
    finally:
        db.close()
