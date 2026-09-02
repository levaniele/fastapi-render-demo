"""
Shared pytest fixtures and configuration for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db_session


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def db_engine():
    """
    Create a test database engine using SQLite in-memory.
    Each test gets a fresh database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(db_engine):
    """
    Create a test database session.
    Automatically rolls back after each test.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def client(db):
    """
    Create a FastAPI TestClient with test database.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "user"
    }


@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin"
    }


@pytest.fixture
def test_tournament_data():
    """Sample tournament data for testing."""
    return {
        "name": "Test Championship 2026",
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "location": "Test Arena",
        "status": "upcoming"
    }


@pytest.fixture
def test_player_data():
    """Sample player data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "gender": "male",
        "birth_date": "1995-05-15"
    }


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_headers(client, test_user_data):
    """
    Create authenticated request headers.
    Registers and logs in a test user, returns headers with auth cookie.
    """
    # Register user
    client.post("/auth/register", json=test_user_data)
    
    # Login
    response = client.post("/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    # Extract auth cookie
    cookies = response.cookies
    return {"Cookie": f"access_token={cookies.get('access_token')}"}


@pytest.fixture
def admin_headers(client, test_admin_data):
    """
    Create authenticated admin request headers.
    """
    # Register admin
    client.post("/auth/register", json=test_admin_data)
    
    # Login
    response = client.post("/auth/login", json={
        "email": test_admin_data["email"],
        "password": test_admin_data["password"]
    })
    
    cookies = response.cookies
    return {"Cookie": f"access_token={cookies.get('access_token')}"}


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
