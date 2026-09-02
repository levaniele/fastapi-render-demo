# Tests Directory Structure

This directory contains all automated tests for the Badminton360 API.

## Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest fixtures
├── unit/                       # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_auth.py           # Auth service unit tests
│   ├── test_tournaments.py    # Tournament service unit tests
│   ├── test_players.py        # Player service unit tests
│   ├── test_rankings.py       # Ranking calculator unit tests
│   └── test_utils.py          # Utility function tests
├── integration/                # Integration tests (with database)
│   ├── __init__.py
│   ├── test_auth_flow.py      # Auth endpoints integration
│   ├── test_tournament_flow.py # Tournament CRUD integration
│   └── test_ranking_flow.py   # Ranking calculation integration
└── e2e/                        # End-to-end tests (full workflows)
    ├── __init__.py
    ├── test_user_journey.py   # Complete user workflows
    └── test_admin_journey.py  # Admin workflows

## Test Types

### Unit Tests (`tests/unit/`)
- Test individual functions/methods in isolation
- Mock external dependencies (database, HTTP clients)
- Fast execution (< 1 second per test)
- No database required

### Integration Tests (`tests/integration/`)
- Test multiple components together
- Use test database
- Verify database interactions
- Moderate execution time (1-5 seconds per test)

### E2E Tests (`tests/e2e/`)
- Test complete user workflows
- Full API request/response cycle
- Test database + business logic + API
- Slower execution (5-30 seconds per test)

## Running Tests

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/               # E2E tests only

# Run specific test file
pytest tests/unit/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run failed tests only
pytest --lf
```

## Writing Tests

### Unit Test Example
```python
# tests/unit/test_auth.py
import pytest
from app.services.auth_service import hash_password, verify_password

def test_hash_password():
    password = "SecurePass123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
```

### Integration Test Example
```python
# tests/integration/test_auth_flow.py
import pytest
from fastapi.testclient import TestClient

def test_login_success(client, test_user):
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.cookies
```

### E2E Test Example
```python
# tests/e2e/test_user_journey.py
def test_complete_tournament_registration(client, test_user):
    # Login
    login_response = client.post("/auth/login", ...)
    
    # Create tournament
    tournament_response = client.post("/tournaments", ...)
    
    # Register player
    register_response = client.post("/tournaments/{id}/register", ...)
    
    # Verify registration
    assert register_response.status_code == 200
```

## Fixtures (`conftest.py`)

Common fixtures available in all tests:
- `client` - FastAPI TestClient
- `db` - Test database session
- `test_user` - Sample user for testing
- `test_tournament` - Sample tournament
- `auth_headers` - Authenticated request headers

## Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Critical paths covered
- **E2E Tests**: Main user workflows covered

## CI/CD Integration

Tests run automatically on:
- Every push to `main` branch
- Every pull request
- Before deployment to production
