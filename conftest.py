"""
Pytest configuration and fixtures for the test suite.
Includes custom HTML report hooks to display API endpoints.
"""
import pytest
from pytest_html import extras

# Hook to add API endpoint information to the HTML report
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    # Add API endpoint to the report's extras (displayed in the Links column)
    if report.when == "call":
        # Extract test function name and map to API endpoints
        test_name = item.nodeid
        endpoint_info = get_endpoint_for_test(test_name)
        
        if endpoint_info:
            report.extra = getattr(report, 'extra', [])
            report.extra.append(extras.url(endpoint_info['url'], endpoint_info['label']))

def get_endpoint_for_test(test_name):
    """Map test names to their corresponding API endpoints."""
    
    # Auth endpoints
    if 'test_register' in test_name:
        return {'url': 'http://localhost:8000/auth/register', 'label': 'POST /auth/register'}
    if 'test_login' in test_name:
        return {'url': 'http://localhost:8000/auth/login', 'label': 'POST /auth/login'}
    if 'test_verify' in test_name:
        return {'url': 'http://localhost:8000/auth/verify', 'label': 'GET /auth/verify'}
    if 'test_logout' in test_name:
        return {'url': 'http://localhost:8000/auth/logout', 'label': 'POST /auth/logout'}
    if 'test_password_reset' in test_name:
        return {'url': 'http://localhost:8000/auth/password/reset', 'label': 'POST /auth/password/*'}
    
    # Tournament endpoints
    if 'test_get_all_tournaments' in test_name:
        return {'url': 'http://localhost:8000/tournaments', 'label': 'GET /tournaments'}
    if 'test_create_tournament' in test_name:
        return {'url': 'http://localhost:8000/tournaments/admin/tournaments', 'label': 'POST /tournaments/admin'}
    if 'test_tournament_sub' in test_name:
        return {'url': 'http://localhost:8000/tournaments/{slug}/stats', 'label': 'GET /tournaments/{slug}/*'}
    
    # Player endpoints
    if 'test_get_all_players' in test_name:
        return {'url': 'http://localhost:8000/players/', 'label': 'GET /players/'}
    if 'test_get_player_by_gender' in test_name:
        return {'url': 'http://localhost:8000/players/gender/Male', 'label': 'GET /players/gender/{gender}'}
    if 'test_get_player_profile' in test_name:
        return {'url': 'http://localhost:8000/players/{slug}', 'label': 'GET /players/{slug}'}
    
    # Club endpoints
    if 'test_get_all_clubs' in test_name:
        return {'url': 'http://localhost:8000/clubs', 'label': 'GET /clubs'}
    if 'test_get_club_by_slug' in test_name:
        return {'url': 'http://localhost:8000/clubs/{slug}', 'label': 'GET /clubs/{slug}'}
    
    # Match endpoints
    if 'test_get_recent_matches' in test_name:
        return {'url': 'http://localhost:8000/matches/recent', 'label': 'GET /matches/recent'}
    if 'test_get_matches_by_category' in test_name:
        return {'url': 'http://localhost:8000/matches/category/MS', 'label': 'GET /matches/category/{cat}'}
    
    # Official endpoints
    if 'test_get_umpires' in test_name:
        return {'url': 'http://localhost:8000/officials/umpires', 'label': 'GET /officials/umpires'}
    if 'test_get_referees' in test_name:
        return {'url': 'http://localhost:8000/officials/referees', 'label': 'GET /officials/referees'}
    
    # Rankings endpoints
    if 'test_get_global_rankings' in test_name:
        return {'url': 'http://localhost:8000/rankings/global', 'label': 'GET /rankings/global'}
    
    # Health endpoints
    if 'test_root' in test_name:
        return {'url': 'http://localhost:8000/', 'label': 'GET /'}
    if 'test_health' in test_name:
        return {'url': 'http://localhost:8000/health', 'label': 'GET /health'}
    
    return None

# Hook to customize the HTML report appearance
def pytest_html_report_title(report):
    report.title = "Badminton360 API Test Report"

@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([
        "<h2>Test Execution Summary</h2>",
        "<p>This report covers automated API endpoint testing for the Badminton360 backend.</p>",
        "<p><strong>Base URL:</strong> http://localhost:8000</p>"
    ])
